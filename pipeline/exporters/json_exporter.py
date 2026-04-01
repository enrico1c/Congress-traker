"""
Export pipeline outputs to JSON artifacts consumed by the Next.js frontend.
"""
import json
import logging
from pathlib import Path
from datetime import datetime

from pipeline.config import ARTIFACTS_DIR, PIPELINE_VERSION

logger = logging.getLogger(__name__)


def _write(filename: str, data: object) -> None:
    path = ARTIFACTS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = path.stat().st_size / 1024
    logger.info(f"[export] Wrote {filename} ({size_kb:.1f} KB)")


def export_all(
    members: list[dict],
    committees: list[dict],
    companies: list[dict],
    trades: list[dict],
    flags: list[dict],
    performance: list[dict],
    data_sources: list[dict],
) -> None:
    """Write all artifact files needed by the frontend."""

    _write("members.json",      members)
    _write("committees.json",   committees)
    _write("companies.json",    companies)
    _write("trades.json",       trades)
    _write("flags.json",        flags)
    _write("performance.json",  performance)

    # Dashboard aggregate
    dashboard = _build_dashboard(members, trades, flags, performance, companies)
    _write("dashboard.json", dashboard)

    # Manifest
    manifest = {
        "generatedAt":     datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipelineVersion": PIPELINE_VERSION,
        "sources":         data_sources,
    }
    _write("manifest.json", manifest)

    logger.info(
        f"[export] Complete: {len(members)} members, "
        f"{len(trades)} trades, {len(flags)} flags, "
        f"{len(companies)} companies"
    )


def _build_dashboard(
    members:     list[dict],
    trades:      list[dict],
    flags:       list[dict],
    performance: list[dict],
    companies:   list[dict],
) -> dict:
    """Build the pre-aggregated dashboard JSON."""

    # Recent trades (last 50 by disclosure date)
    recent_trades = sorted(
        trades,
        key=lambda t: t.get("disclosureDate", ""),
        reverse=True,
    )[:50]

    # Top traders by trade count
    from collections import Counter
    member_counts = Counter(t["memberId"] for t in trades)
    top_trader_ids = [mid for mid, _ in member_counts.most_common(10)]
    top_traders = []
    member_map = {m["id"]: m for m in members}
    for mid in top_trader_ids:
        m = member_map.get(mid)
        if m:
            top_traders.append({
                "memberId":   m["id"],
                "memberName": m["name"],
                "memberSlug": m["slug"],
                "tradeCount": member_counts[mid],
                "party":      m["party"],
            })

    # Top performers
    sorted_perf = sorted(
        [p for p in performance if p.get("estimatedReturn1y") is not None],
        key=lambda p: p.get("estimatedReturn1y", -999),
        reverse=True,
    )[:10]
    top_performers = [
        {
            "memberId":   p["memberId"],
            "memberName": p["memberName"],
            "memberSlug": p["memberSlug"],
            "badge":      p["badge"],
            "return1y":   p.get("estimatedReturn1y"),
        }
        for p in sorted_perf
    ]

    # Most traded companies
    ticker_counts = Counter(t["ticker"] for t in trades if t.get("ticker"))
    top_companies = []
    company_map = {c["ticker"]: c for c in companies}
    for ticker, cnt in ticker_counts.most_common(10):
        co = company_map.get(ticker, {})
        top_companies.append({
            "ticker":      ticker,
            "companyName": co.get("name", ticker),
            "tradeCount":  cnt,
            "sector":      co.get("sector", "Unknown"),
        })

    # Trades by policy area
    pa_trade_map: dict[str, dict] = {}
    from pipeline.config import SECTOR_TO_POLICY_AREAS
    for trade in trades:
        sector = trade.get("sector", "Unknown")
        pas = SECTOR_TO_POLICY_AREAS.get(sector, [])
        for pa in pas:
            if pa not in pa_trade_map:
                pa_trade_map[pa] = {"policyArea": pa, "tradeCount": 0, "flaggedCount": 0}
            pa_trade_map[pa]["tradeCount"] += 1
    for flag in flags:
        for pa in flag.get("matchedPolicyAreas", []):
            if pa in pa_trade_map:
                pa_trade_map[pa]["flaggedCount"] += 1
    trades_by_pa = sorted(pa_trade_map.values(), key=lambda x: x["tradeCount"], reverse=True)

    # Activity timeline (monthly)
    month_map: dict[str, dict] = {}
    for trade in trades:
        month = (trade.get("tradeDate") or trade.get("disclosureDate") or "")[:7]
        if not month:
            continue
        if month not in month_map:
            month_map[month] = {"month": month, "purchases": 0, "sales": 0, "total": 0}
        if "Purchase" in (trade.get("tradeType") or ""):
            month_map[month]["purchases"] += 1
        else:
            month_map[month]["sales"] += 1
        month_map[month]["total"] += 1
    activity_timeline = sorted(month_map.values(), key=lambda x: x["month"])

    # Trades by sector
    sector_map: dict[str, dict] = {}
    flag_ticker_set = {f["ticker"] for f in flags}
    for trade in trades:
        sector = trade.get("sector", "Unknown")
        if sector not in sector_map:
            sector_map[sector] = {"sector": sector, "count": 0, "flaggedCount": 0}
        sector_map[sector]["count"] += 1
        if trade.get("ticker") in flag_ticker_set:
            sector_map[sector]["flaggedCount"] += 1
    trades_by_sector = sorted(sector_map.values(), key=lambda x: x["count"], reverse=True)

    return {
        "totalMembers":          len(members),
        "totalTrades":           len(trades),
        "totalFlaggedTrades":    len(flags),
        "totalCompanies":        len(companies),
        "lastUpdated":           datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recentTrades":          recent_trades,
        "topTraders":            top_traders,
        "topPerformers":         top_performers,
        "mostTradedCompanies":   top_companies,
        "tradesByPolicyArea":    trades_by_pa,
        "activityTimeline":      activity_timeline[-24:],  # last 24 months
        "tradesBySector":        trades_by_sector[:12],
    }
