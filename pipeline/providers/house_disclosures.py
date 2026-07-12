"""
House STOCK Act Periodic Transaction Report (PTR) provider.

Primary source: github.com/TattooedHead/house-stock-watcher-data
- No API key required
- Free, actively-maintained GitHub mirror that already parses individual
  House PTR PDFs (disclosures-clerk.house.gov/public_disc/ptr-pdfs/) into
  structured per-transaction JSON — verified live and current as of
  2026-07-11.
- Chosen over scraping the government PDFs ourselves: the real annual ZIP
  at disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip
  (the previous domain, disclosures.house.gov, now redirects to an
  unrelated Lobbying Disclosure system) only contains a filer *index*
  (name/filing-type/DocID), not transaction line items — actual PTR trades
  are one PDF per filing, needing real per-document table parsing that
  doesn't exist anywhere in this pipeline. Reusing an already-solved mirror
  is simpler and fresher than building that from scratch.

Fallback: QuiverQuantitative (requires QUIVER_API_KEY as of 2026 — its
live/bulk endpoints now return 401 without one; kept in case a key is ever
configured).
"""
import re
import logging
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from pipeline.config import (
    RAW_DIR,
    ARTIFACTS_DIR,
    REQUEST_TIMEOUT,
    REQUEST_MAX_RETRIES,
    USER_AGENT,
    AMOUNT_RANGES,
    USE_CACHE,
    YEARS_BACK,
)

logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})

HOUSE_WATCHER_MIRROR_URL = (
    "https://raw.githubusercontent.com/TattooedHead/house-stock-watcher-data"
    "/main/data/all_transactions.json"
)


@retry(stop=stop_after_attempt(REQUEST_MAX_RETRIES), wait=wait_exponential(min=1, max=8))
def _get(url: str, **kwargs) -> requests.Response:
    resp = SESSION.get(url, timeout=REQUEST_TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp


def _fetch_via_house_watcher_mirror(years_back: int) -> list[dict]:
    """Fetch + normalize the house-stock-watcher-data mirror's flat transaction list."""
    resp = _get(HOUSE_WATCHER_MIRROR_URL)
    records = resp.json()
    if not isinstance(records, list):
        raise ValueError("Unexpected mirror response shape (expected a JSON list)")

    cutoff_year = datetime.now().year - years_back
    out = []
    for r in records:
        trade_type = _normalize_trade_type(r.get("type", ""))
        if not trade_type:
            continue
        trade_date = _normalize_date(r.get("transaction_date", ""))
        filing_year = int(trade_date[:4]) if trade_date else datetime.now().year
        if filing_year < cutoff_year:
            continue
        amount_label = r.get("amount") or ""
        amount = _parse_amount(amount_label)
        out.append({
            "source": "house",
            "member_name": r.get("representative", ""),
            "member_id": r.get("filing_id", ""),
            "asset_name": r.get("asset_description", "") or r.get("ticker", ""),
            "ticker": (r.get("ticker") or "").strip().upper(),
            "trade_type": trade_type,
            "raw_amount": amount_label,
            "amount_min": amount.get("min"),
            "amount_max": amount.get("max"),
            "amount_label": amount.get("label", amount_label),
            "trade_date": trade_date,
            "disclosure_date": _normalize_date(r.get("disclosure_date", "")),
            "asset_type": r.get("asset_type") or "Stock",
            "filing_year": filing_year,
            "source_url": r.get("source_url") or "https://disclosures-clerk.house.gov/",
        })
    return out


def _normalize_trade_type(raw: str) -> str | None:
    raw_l = raw.lower()
    if any(x in raw_l for x in ["purchase", "buy", "p -"]):
        return "Purchase"
    if "partial" in raw_l or "s_partial" in raw_l:
        return "Sale (Partial)"
    if any(x in raw_l for x in ["sale", "sell", "sold", "s -"]):
        return "Sale"
    if "exchange" in raw_l:
        return "Exchange"
    return None  # skip gifts, transfers, etc.


def _parse_amount(raw: str) -> dict:
    """Map a raw STOCK Act amount code to a structured range dict."""
    raw = raw.strip()
    # Check direct code match
    if raw in AMOUNT_RANGES:
        return AMOUNT_RANGES[raw]
    # Check label match
    for _code, rng in AMOUNT_RANGES.items():
        if rng["label"].lower() in raw.lower():
            return rng
    # Try to parse dollar values from the string
    nums = re.findall(r"[\d,]+", raw.replace("$", ""))
    if len(nums) >= 2:
        try:
            lo = int(nums[0].replace(",", ""))
            hi = int(nums[1].replace(",", ""))
            return {"min": lo, "max": hi, "label": f"${lo:,} - ${hi:,}"}
        except ValueError:
            pass
    # Default: unknown range
    return {"min": 1001, "max": 15000, "label": "$1,001 - $15,000"}


def _normalize_date(raw: str) -> str | None:
    """Normalize various date formats to ISO YYYY-MM-DD."""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


# QuiverQuantitative — kept as a secondary fallback in case QUIVER_API_KEY is
# ever configured (its live/bulk endpoints now require auth; see fetch_all_house).
QUIVER_BASE = "https://api.quiverquant.com/beta"
QUIVER_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _fetch_via_quiver_all() -> list[dict]:
    """
    Fetch Congress trades from QuiverQuantitative's API (both chambers).
    Returns [] on any failure — callers fall through to their next source.
    Does NOT fall back to a committed cache file here: doing so previously
    made a total QuiverQuant failure look identical to a successful fetch
    (same return shape, no exception), so callers kept re-serving a
    months-stale cache as if it were fresh instead of trying their real
    fallback. Last-resort stale-cache use, if ever wanted again, belongs in
    the caller where it can be logged honestly as "stale", not masked here.
    """
    transactions = []
    quiver_ok = False

    logger.info("[quiver] Fetching Congress trades from QuiverQuantitative...")
    headers = {"User-Agent": QUIVER_BROWSER_UA, "Accept": "application/json"}
    for endpoint in ["live", "bulk"]:
        try:
            url = f"{QUIVER_BASE}/{endpoint}/congresstrading"
            resp = SESSION.get(url, headers=headers, timeout=60)
            resp.raise_for_status()
            records = resp.json()
            if not isinstance(records, list):
                continue
            logger.info(f"[quiver] {endpoint}: {len(records)} records")
            for rec in records:
                txn = _normalize_quiver_record(rec)
                if txn:
                    transactions.append(txn)
            quiver_ok = True
        except Exception as e:
            logger.warning(f"[quiver] {endpoint} endpoint failed: {e}")

    if not quiver_ok:
        return []

    seen = set()
    unique = []
    for t in transactions:
        key = (t["member_name"], t["ticker"], t["trade_date"], t["trade_type"])
        if key not in seen:
            seen.add(key)
            unique.append(t)
    logger.info(f"[quiver] Fetched {len(unique)} unique transactions")
    return unique


def _normalize_quiver_record(rec: dict) -> dict | None:
    """Normalize a QuiverQuant Congress trade record to the pipeline's standard format."""
    trade_type_raw = rec.get("Transaction", "")
    trade_type = _normalize_trade_type(trade_type_raw)
    if not trade_type:
        return None

    member_name = (rec.get("Representative") or "").strip()
    bio_id = rec.get("BioGuideID", "")
    chamber_raw = rec.get("House", "")
    ticker = (rec.get("Ticker") or "").strip().upper()
    tx_date = _normalize_date(rec.get("TransactionDate") or rec.get("ReportDate") or "")
    disc_date = _normalize_date(rec.get("ReportDate") or "")
    amount_label = rec.get("Range") or ""
    amount = _parse_amount(amount_label)
    asset_type = rec.get("TickerType") or "Stock"
    source = "senate" if "senate" in chamber_raw.lower() else "house"

    return {
        "source": source,
        "member_name": member_name,
        "member_id": bio_id,
        "asset_name": rec.get("Description") or ticker,
        "ticker": ticker,
        "trade_type": trade_type,
        "raw_amount": amount_label,
        "amount_min": amount.get("min"),
        "amount_max": amount.get("max"),
        "amount_label": amount.get("label", amount_label),
        "trade_date": tx_date,
        "disclosure_date": disc_date,
        "asset_type": asset_type,
        "filing_year": int(tx_date[:4]) if tx_date and len(tx_date) >= 4 else datetime.now().year,
        "source_url": "https://efdsearch.senate.gov/" if source == "senate"
                      else "https://disclosures-clerk.house.gov/",
    }


def fetch_all_house(years_back: int = 5) -> list[dict]:
    """
    Fetch House PTR trade disclosures.
    Primary:   house-stock-watcher-data mirror (free, keyless, verified fresh).
    Fallback:  QuiverQuantitative (needs QUIVER_API_KEY).
    Returns ALL records (House + Senate) when sourced via QuiverQuant, since
    that API mixes both chambers; main.py's resolver filters by chamber.
    """
    try:
        records = _fetch_via_house_watcher_mirror(years_back)
        if records:
            logger.info(f"[house] {len(records)} House trades via house-stock-watcher-data mirror")
            return records
    except Exception as e:
        logger.warning(f"[house] house-stock-watcher-data mirror failed: {e}")

    try:
        all_records = _fetch_via_quiver_all()
        house_records = [r for r in all_records if r.get("source") == "house"]
        if house_records:
            logger.info(f"[house] {len(house_records)} House trades via QuiverQuant")
            return all_records
    except Exception as e:
        logger.warning(f"[house] QuiverQuant failed: {e}")

    logger.error("[house] All House data sources failed — no House data fetched this run")
    return []
