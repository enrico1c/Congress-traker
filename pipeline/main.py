"""
Congress Trades — Main Pipeline Runner

Usage:
  python main.py                     # Full pipeline (fetch + process + export)
  python main.py --step fetch        # Only fetch raw data
  python main.py --step process      # Only process/normalize (uses cached raw)
  python main.py --step export       # Only export artifacts (uses cached processed)
  python main.py --seed              # Generate sample data (no network needed)

Data flow:
  1. Fetch: House ZIP + Senate EFTS + unitedstates/congress → raw JSON cache
  2. Normalize: resolve members + tickers + compute sectors
  3. Score: flag trades with policy-overlap scores
  4. Estimate: compute portfolio performance
  5. Export: write data/artifacts/*.json for frontend

All network calls are retried and cached. Running with PIPELINE_USE_CACHE=true
(default) will use cached data on subsequent runs, only fetching new data.
"""
import json
import logging
import sys
import time
import hashlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import click

# Setup path so we can import from pipeline/*
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.config import (
    YEARS_BACK,
    LOG_LEVEL,
    ARTIFACTS_DIR,
    PROCESSED_DIR,
    SECTOR_TO_POLICY_AREAS,
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline.main")


@click.command()
@click.option("--step", type=click.Choice(["fetch", "process", "export", "all"]), default="all")
@click.option("--seed", is_flag=True, help="Generate seed/sample data instead of fetching live")
@click.option("--years", default=YEARS_BACK, help="Years of history to fetch")
def main(step: str, seed: bool, years: int):
    """Congress Trades data pipeline."""
    start = time.time()

    if seed:
        logger.info("Generating seed data…")
        _run_seed()
        logger.info(f"Seed complete in {time.time() - start:.1f}s")
        return

    if step in ("fetch", "all"):
        logger.info("=== Step 1: Fetch ===")
        _run_fetch(years)

    if step in ("process", "all"):
        logger.info("=== Step 2: Process ===")
        _run_process()

    if step in ("export", "all"):
        logger.info("=== Step 3: Export ===")
        _run_export()

    logger.info(f"Pipeline complete in {time.time() - start:.1f}s")


def _run_fetch(years: int):
    from pipeline.providers import house_disclosures, senate_disclosures, congress_members, market_data

    # Fetch disclosures
    logger.info(f"Fetching House disclosures ({years} years)…")
    house_txns = house_disclosures.fetch_all_house(years)
    _save_processed("raw_house.json", house_txns)

    logger.info("Fetching Senate disclosures…")
    senate_txns = senate_disclosures.fetch_all_senate(years)
    _save_processed("raw_senate.json", senate_txns)

    # Fetch member metadata
    logger.info("Fetching member + committee data…")
    current_members = congress_members.fetch_current_members()
    historical_members = congress_members.fetch_historical_members()
    committees_raw = congress_members.fetch_committees()
    membership_raw = congress_members.fetch_committee_membership()
    _save_processed("raw_members_current.json", current_members)
    _save_processed("raw_members_historical.json", historical_members)
    _save_processed("raw_committees.json", committees_raw)
    _save_processed("raw_membership.json", membership_raw)

    # Fetch SEC ticker map
    logger.info("Fetching SEC ticker map…")
    ticker_map = market_data.get_sec_ticker_map()
    # Ticker map already cached in RAW_DIR

    logger.info("Fetch complete.")


def _run_process():
    from pipeline.providers import congress_members, market_data
    from pipeline.normalizers.member_resolver import MemberResolver
    from pipeline.normalizers.ticker_resolver import TickerResolver

    # Load raw data
    house_txns     = _load_processed("raw_house.json") or []
    senate_txns    = _load_processed("raw_senate.json") or []
    members_raw    = _load_processed("raw_members_current.json") or []
    hist_raw       = _load_processed("raw_members_historical.json") or []
    committees_raw = _load_processed("raw_committees.json") or []
    membership_raw = _load_processed("raw_membership.json") or {}

    all_raw_members = members_raw + hist_raw

    logger.info(f"Raw: {len(house_txns)} house + {len(senate_txns)} senate txns, {len(all_raw_members)} members")

    # Normalize members and committees
    canonical_members = congress_members.normalize_members(all_raw_members)
    canonical_committees = congress_members.normalize_committees(committees_raw, membership_raw)
    member_committee_map = congress_members.build_member_committee_map(canonical_members, canonical_committees)

    # Enrich members with committee assignments and policy areas
    for m in canonical_members:
        mid = m["id"]
        committees = member_committee_map.get(mid, [])
        m["committees"] = committees
        # Collect policy areas from all committee assignments
        all_pas = []
        for c in committees:
            all_pas.extend(c.get("policy_areas", []))
        # Deduplicate
        seen = set()
        m["policy_areas"] = [pa for pa in all_pas if not (pa in seen or seen.add(pa))]

    # Resolve members in trade disclosures
    resolver = MemberResolver(canonical_members)

    # Load SEC ticker map for ticker resolution
    from pipeline.config import RAW_DIR
    sec_map_file = RAW_DIR / "sec_ticker_map.json"
    sec_map = {}
    if sec_map_file.exists():
        with open(sec_map_file) as f:
            sec_map = json.load(f)
    ticker_resolver = TickerResolver(sec_map)

    all_raw_txns = house_txns + senate_txns
    logger.info(f"Processing {len(all_raw_txns)} raw transactions…")

    # Collect tickers needing company info
    tickers_to_lookup = set()
    resolved_txns = []

    for raw in all_raw_txns:
        member_name = raw.get("member_name", "")
        state = raw.get("state", "")
        chamber = raw.get("source") == "house" and "House" or "Senate"
        member = resolver.resolve(member_name, state, chamber)
        if not member:
            continue

        ticker = ticker_resolver.resolve(
            raw.get("ticker", ""),
            raw.get("asset_name", ""),
        )
        if ticker:
            tickers_to_lookup.add(ticker)

        resolved_txns.append({**raw, "_resolved_member_id": member["id"], "_resolved_ticker": ticker})

    logger.info(f"Resolved {len(resolved_txns)} transactions to known members")
    logger.info(f"Unique tickers to fetch: {len(tickers_to_lookup)}")

    # Fetch company info for all tickers
    company_info_map = market_data.bulk_get_company_info(list(tickers_to_lookup))

    # Build canonical trades
    canonical_trades = []
    member_map = {m["id"]: m for m in canonical_members}

    for raw in resolved_txns:
        mid     = raw["_resolved_member_id"]
        ticker  = raw["_resolved_ticker"]
        member  = member_map.get(mid)
        company = company_info_map.get(ticker, {}) if ticker else {}

        if not member:
            continue

        trade_date = raw.get("trade_date")
        disc_date  = raw.get("disclosure_date")
        delay      = raw.get("disclosure_delay_days")
        if not delay and trade_date and disc_date:
            try:
                d1 = datetime.strptime(trade_date, "%Y-%m-%d")
                d2 = datetime.strptime(disc_date, "%Y-%m-%d")
                delay = (d2 - d1).days
            except Exception:
                delay = None

        trade_id = _make_id(mid, ticker, trade_date, raw.get("trade_type", ""))

        trade = {
            "id":               trade_id,
            "memberId":         mid,
            "memberName":       member["name"],
            "memberSlug":       member["slug"],
            "memberParty":      member["party"],
            "memberChamber":    member["chamber"],
            "memberState":      member["state"],
            "ticker":           ticker or raw.get("asset_name", "")[:10],
            "companyName":      company.get("name", raw.get("asset_name", "")),
            "sector":           company.get("sector", "Unknown"),
            "industry":         company.get("industry", "Unknown"),
            "tradeType":        raw.get("trade_type", ""),
            "tradeDate":        trade_date or disc_date or "",
            "dateApproximate":  not bool(trade_date),
            "disclosureDate":   disc_date or "",
            "disclosureDelay":  delay or 0,
            "amount": {
                "min":   raw.get("amount_min") or 1001,
                "max":   raw.get("amount_max") or 15000,
                "label": raw.get("amount_label") or "$1,001 - $15,000",
            },
            "assetType":  raw.get("asset_type", "Stock"),
            "comment":    raw.get("comment", ""),
            "sourceUrl":  raw.get("source_url", ""),
            "isFlagged":  False,
            "flagScore":  None,
            "flagSeverity": None,
        }
        canonical_trades.append(trade)

    logger.info(f"Built {len(canonical_trades)} canonical trades")

    # Build canonical companies
    company_trade_counts: dict[str, dict] = defaultdict(lambda: {"tradeCount": 0, "buyCount": 0, "sellCount": 0, "traders": set(), "flagged": 0})
    for t in canonical_trades:
        tk = t["ticker"]
        company_trade_counts[tk]["tradeCount"] += 1
        if t["tradeType"].startswith("Purchase"):
            company_trade_counts[tk]["buyCount"] += 1
        else:
            company_trade_counts[tk]["sellCount"] += 1
        company_trade_counts[tk]["traders"].add(t["memberId"])

    canonical_companies = []
    for tk, ci in company_info_map.items():
        counts = company_trade_counts.get(tk, {})
        sector = ci.get("sector", "Unknown")
        canonical_companies.append({
            "ticker":           tk,
            "name":             ci.get("name", tk),
            "sector":           sector,
            "industry":         ci.get("industry", "Unknown"),
            "policy_areas":     SECTOR_TO_POLICY_AREAS.get(sector, []),
            "marketCap":        ci.get("market_cap"),
            "tradeCount":       counts.get("tradeCount", 0),
            "flaggedTradeCount": 0,  # updated after scoring
            "uniqueTraders":    len(counts.get("traders", set())),
            "buyCount":         counts.get("buyCount", 0),
            "sellCount":        counts.get("sellCount", 0),
        })
    # Convert set to int for JSON serialization
    for co in canonical_companies:
        if isinstance(co.get("uniqueTraders"), set):
            co["uniqueTraders"] = len(co["uniqueTraders"])

    logger.info(f"Built {len(canonical_companies)} canonical companies")

    # Save processed data for export step
    _save_processed("members.json",    canonical_members)
    _save_processed("committees.json", canonical_committees)
    _save_processed("companies.json",  canonical_companies)
    _save_processed("trades.json",     canonical_trades)

    logger.info("Process complete.")


def _run_export():
    from pipeline.engines import overlap_scorer, performance_estimator
    from pipeline.providers import market_data
    from pipeline.exporters import json_exporter

    members    = _load_processed("members.json") or []
    committees = _load_processed("committees.json") or []
    companies  = _load_processed("companies.json") or []
    trades     = _load_processed("trades.json") or []

    member_map  = {m["id"]: m for m in members}
    company_map = {c["ticker"]: c for c in companies}

    # Build member trade lists for concentration scoring
    member_trades: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        member_trades[t["memberId"]].append(t)

    # Score trades for policy overlap
    logger.info("Scoring policy overlaps…")
    flags = []
    for trade in trades:
        member  = member_map.get(trade["memberId"])
        company = company_map.get(trade["ticker"])
        if not member or not company:
            continue

        flag = overlap_scorer.score_trade(
            trade=trade,
            member=member,
            company=company,
            all_member_trades=member_trades[trade["memberId"]],
        )
        if flag:
            trade["isFlagged"]   = True
            trade["flagScore"]   = flag["overallScore"]
            trade["flagSeverity"] = flag["severity"]
            flags.append(flag)

    logger.info(f"Flagged {len(flags)} trades")

    # Update company flagged counts
    flag_ticker_counts = defaultdict(int)
    for f in flags:
        flag_ticker_counts[f["ticker"]] += 1
    for co in companies:
        co["flaggedTradeCount"] = flag_ticker_counts.get(co["ticker"], 0)

    # Enrich members with aggregate stats
    for m in members:
        mid = m["id"]
        mtrades = member_trades[mid]
        mflags  = [f for f in flags if f["memberId"] == mid]
        m["tradeCount"]        = len(mtrades)
        m["flaggedTradeCount"] = len(mflags)
        m["totalValueMin"]     = sum(t["amount"]["min"] for t in mtrades)
        m["totalValueMax"]     = sum(t["amount"]["max"] for t in mtrades)
        # Last disclosure
        disc_dates = [t["disclosureDate"] for t in mtrades if t["disclosureDate"]]
        m["lastDisclosureDate"] = max(disc_dates) if disc_dates else None

    # Estimate portfolio performance
    logger.info("Estimating portfolio performance…")
    sp500_returns = market_data.get_sp500_returns()

    # Fetch price histories for all tickers (already cached)
    unique_tickers = list({t["ticker"] for t in trades if t.get("ticker")})
    price_histories: dict[str, dict] = {}
    for i, tk in enumerate(unique_tickers):
        if i % 50 == 0:
            logger.info(f"  Loading prices {i}/{len(unique_tickers)}…")
        price_histories[tk] = market_data.get_price_history(tk)

    performance_snapshots = []
    for m in members:
        mid = m["id"]
        snap = performance_estimator.estimate_member_performance(
            member=m,
            trades=member_trades[mid],
            price_histories=price_histories,
            sp500_returns=sp500_returns,
        )
        performance_snapshots.append(snap)
        # Update member badge
        m["estimatedReturn1y"]   = snap.get("estimatedReturn1y")
        m["estimatedReturn3y"]   = snap.get("estimatedReturn3y")
        m["estimatedReturn5y"]   = snap.get("estimatedReturn5y")
        m["performanceBadge"]    = snap["badge"]
        m["performanceConfidence"] = snap["confidence"]

    # Build data source status
    data_sources = [
        {"name": "House STOCK Act PTR", "url": "https://disclosures.house.gov",  "requiresKey": False, "healthy": True, "notes": "Annual ZIP + XML files"},
        {"name": "Senate EFTS API",     "url": "https://efts.senate.gov",       "requiresKey": False, "healthy": True, "notes": "JSON REST API, no key"},
        {"name": "unitedstates/congress","url": "https://unitedstates.github.io","requiresKey": False, "healthy": True, "notes": "Public domain member + committee data"},
        {"name": "Yahoo Finance",       "url": "https://finance.yahoo.com",     "requiresKey": False, "healthy": True, "notes": "Prices + sector data via yfinance"},
        {"name": "SEC EDGAR tickers",   "url": "https://www.sec.gov/files/company_tickers.json", "requiresKey": False, "healthy": True, "notes": "Official ticker → company map"},
    ]

    json_exporter.export_all(
        members=members,
        committees=committees,
        companies=companies,
        trades=trades,
        flags=flags,
        performance=performance_snapshots,
        data_sources=data_sources,
    )

    logger.info("Export complete.")


def _run_seed():
    """Generate realistic sample data for development/demo without network calls."""
    from scripts.seed_data import generate_seed_data
    generate_seed_data()


def _save_processed(filename: str, data: object) -> None:
    path = PROCESSED_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, default=str)


def _load_processed(filename: str) -> object | None:
    path = PROCESSED_DIR / filename
    if not path.exists():
        logger.warning(f"[main] Processed file not found: {filename}")
        return None
    with open(path) as f:
        return json.load(f)


def _make_id(*parts) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


if __name__ == "__main__":
    main()
