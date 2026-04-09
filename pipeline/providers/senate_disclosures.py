"""
Senate EFTS (Electronic Filing & Tracking System) provider.

Primary source: https://efts.senate.gov/LATEST/search-index
- NO API key required
- Public JSON REST API with pagination
- Returns structured trade disclosure data

Documentation: https://efts.senate.gov/
"""
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from pipeline.config import (
    SENATE_EFTS_BASE,
    RAW_DIR,
    REQUEST_TIMEOUT,
    REQUEST_MAX_RETRIES,
    USER_AGENT,
    AMOUNT_RANGES,
    USE_CACHE,
    YEARS_BACK,
)

logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

SENATE_SEARCH_URL = "https://efts.senate.gov/LATEST/search-index"
SENATE_DISCLOSURE_BASE = "https://efts.senate.gov"

# Transaction report type IDs used by Senate EFTS
PTR_TYPE_ID = "11"   # Periodic Transaction Report (trades)


# Senate EFTS may block standard bot User-Agents or have SSL quirks from GitHub Actions IPs.
# Use a browser-like UA and disable SSL verification as fallback.
SENATE_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@retry(stop=stop_after_attempt(REQUEST_MAX_RETRIES), wait=wait_exponential(min=1, max=8))
def _search(params: dict) -> dict:
    import urllib3
    try:
        resp = SESSION.get(SENATE_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Fallback: browser UA + skip SSL verification (government cert may fail from cloud IPs)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resp = SESSION.get(
            SENATE_SEARCH_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            verify=False,
            headers={"User-Agent": SENATE_BROWSER_UA, "Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


def fetch_senate_transactions(
    from_date: str,
    to_date: str,
    page_size: int = 100,
) -> list[dict]:
    """
    Fetch Senate periodic transaction reports via EFTS API.

    Args:
        from_date: ISO date string YYYY-MM-DD
        to_date:   ISO date string YYYY-MM-DD

    Returns list of raw transaction dicts.
    """
    cache_key = f"senate_{from_date}_{to_date}.json"
    cache_file = RAW_DIR / cache_key

    if USE_CACHE and cache_file.exists():
        logger.info(f"[senate] Using cached data for {from_date}→{to_date}")
        with open(cache_file) as f:
            return json.load(f)

    all_txns: list[dict] = []
    offset = 0
    total = None

    while True:
        params = {
            "q": "",
            "dateRange": "custom",
            "fromDate": from_date,
            "toDate": to_date,
            "pageSize": page_size,
            "offset": offset,
        }

        try:
            logger.info(f"[senate] Fetching page offset={offset} ({from_date}→{to_date})")
            data = _search(params)
        except Exception as e:
            logger.error(f"[senate] Fetch failed at offset={offset}: {e}")
            break

        hits = data.get("hits", {})
        records = hits.get("hits", [])

        if total is None:
            total = hits.get("total", {}).get("value", 0)
            logger.info(f"[senate] Total records available: {total}")

        for rec in records:
            source = rec.get("_source", {})
            txns = _parse_senate_record(source)
            all_txns.extend(txns)

        offset += page_size
        if offset >= (total or 0) or not records:
            break

        time.sleep(0.3)  # polite rate-limiting

    logger.info(f"[senate] Fetched {len(all_txns)} transactions")

    with open(cache_file, "w") as f:
        json.dump(all_txns, f)

    return all_txns


def _parse_senate_record(source: dict) -> list[dict]:
    """
    Parse a single EFTS search result record into normalized transaction dicts.

    EFTS record structure (approximate):
    {
      "first_name": str,
      "last_name": str,
      "senator_id": str,
      "transaction_date": str,
      "date_received": str,
      "asset_description": str,
      "asset_type": str,
      "type": str,          # "Purchase", "Sale", etc.
      "amount": str,        # range label
      "comment": str,
      "link": str,          # link to original PDF
    }
    """
    txns = []

    first = source.get("first_name", "")
    last  = source.get("last_name", "")
    name  = f"{first} {last}".strip()
    senator_id = source.get("senator_id", "")

    # EFTS may return multiple transactions in one filing
    # Check if there's a `transactions` list or just one record
    raw_txns_list = source.get("transactions", [source])

    for raw in raw_txns_list:
        asset    = raw.get("asset_description", "") or source.get("asset_description", "")
        asset_type = raw.get("asset_type", "Stock") or source.get("asset_type", "Stock")
        tx_type  = raw.get("type", "") or source.get("type", "")
        amount   = raw.get("amount", "") or source.get("amount", "")
        tx_date  = raw.get("transaction_date", "") or source.get("transaction_date", "")
        disc_date = raw.get("date_received", "") or source.get("date_received", "")
        comment  = raw.get("comment", "") or source.get("comment", "")
        link     = raw.get("link", "") or source.get("link", "")

        # Normalize type
        tx_type_norm = _normalize_type(tx_type)
        if not tx_type_norm:
            continue

        # Try to extract ticker from asset description
        ticker = _extract_ticker(asset)

        amount_dict = _parse_amount_label(amount)
        tx_date_norm  = _normalize_date(tx_date)
        disc_date_norm = _normalize_date(disc_date)

        # Calculate disclosure delay
        delay = None
        if tx_date_norm and disc_date_norm:
            try:
                d1 = datetime.strptime(tx_date_norm, "%Y-%m-%d")
                d2 = datetime.strptime(disc_date_norm, "%Y-%m-%d")
                delay = (d2 - d1).days
            except ValueError:
                pass

        source_url = link or "https://efts.senate.gov/"
        if link and not link.startswith("http"):
            source_url = f"https://efts.senate.gov/{link.lstrip('/')}"

        txns.append({
            "source": "senate",
            "member_name": name,
            "member_id": senator_id,
            "asset_name": asset,
            "ticker": ticker,
            "trade_type": tx_type_norm,
            "raw_amount": amount,
            "amount_min": amount_dict.get("min"),
            "amount_max": amount_dict.get("max"),
            "amount_label": amount_dict.get("label", amount),
            "trade_date": tx_date_norm,
            "disclosure_date": disc_date_norm,
            "disclosure_delay_days": delay,
            "asset_type": asset_type,
            "comment": comment,
            "source_url": source_url,
        })

    return txns


def _normalize_type(raw: str) -> str | None:
    raw_l = (raw or "").lower()
    if any(x in raw_l for x in ["purchase", "buy"]):
        return "Purchase"
    if "partial" in raw_l:
        return "Sale (Partial)"
    if any(x in raw_l for x in ["sale", "sell", "sold"]):
        return "Sale"
    if "exchange" in raw_l:
        return "Exchange"
    return None


def _extract_ticker(asset_description: str) -> str:
    """Try to extract a ticker symbol from an asset description string."""
    import re
    if not asset_description:
        return ""
    # Look for patterns like "(AAPL)", "[MSFT]", or standalone uppercase 1-5 letter words
    patterns = [
        r"\(([A-Z]{1,5})\)",   # (AAPL)
        r"\[([A-Z]{1,5})\]",   # [MSFT]
        r"\b([A-Z]{2,5})\b",   # standalone UPPER word
    ]
    for pattern in patterns:
        match = re.search(pattern, asset_description)
        if match:
            candidate = match.group(1)
            # Filter out common non-ticker words
            if candidate not in {"INC", "LLC", "CORP", "LTD", "CO", "THE", "AND", "FOR", "IN", "OF"}:
                return candidate
    return ""


def _parse_amount_label(raw: str) -> dict:
    """Parse Senate amount range string to structured dict."""
    import re
    raw = (raw or "").strip()
    for _code, rng in AMOUNT_RANGES.items():
        if rng["label"].lower() == raw.lower():
            return rng
    # Try parsing dollar values
    nums = re.findall(r"[\d,]+", raw.replace("$", ""))
    if len(nums) >= 2:
        try:
            lo = int(nums[0].replace(",", ""))
            hi = int(nums[1].replace(",", ""))
            return {"min": lo, "max": hi, "label": f"${lo:,} - ${hi:,}"}
        except ValueError:
            pass
    return {"min": 1001, "max": 15000, "label": "$1,001 - $15,000"}


def _normalize_date(raw: str) -> str | None:
    if not raw:
        return None
    raw = raw.strip().split("T")[0]  # strip time component
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def fetch_all_senate(years_back: int = 5) -> list[dict]:
    """Fetch Senate trade data for the past N years."""
    from_date = (datetime.now() - timedelta(days=years_back * 365)).strftime("%Y-%m-%d")
    to_date   = datetime.now().strftime("%Y-%m-%d")
    return fetch_senate_transactions(from_date, to_date)
