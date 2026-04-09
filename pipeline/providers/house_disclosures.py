"""
House STOCK Act Periodic Transaction Report (PTR) provider.

Primary source: https://disclosures.house.gov/
- No API key required
- Provides downloadable ZIP archives containing XML files per disclosure
- Official U.S. House of Representatives data

Data structure:
  Each year has a ZIP file at:
    https://disclosures.house.gov/FinancialDisclosure/PressSummary?year=YYYY
  Inside: one XML file per filer containing their transactions.

Fallback:
  If ZIP fetch fails, try the searchable form with a date range.
"""
import io
import re
import time
import zipfile
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator
import xml.etree.ElementTree as ET

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from pipeline.config import (
    HOUSE_DISCLOSURE_BASE,
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
SESSION.headers.update({"User-Agent": USER_AGENT})

# PTR (Periodic Transaction Reports) data — these are the individual trade disclosures
# The House provides an annual summary and per-member XML files
HOUSE_PTR_INDEX_URL = "{base}/FinancialDisclosure/ViewMemberSearchResult"
HOUSE_PTR_DOWNLOAD_URL = "{base}/FinancialDisclosure/PressSummary?year={year}"

# The actual downloadable data for a given year
# Pattern: https://disclosures.house.gov/public_disc/ptr-pdfs/{year}/
HOUSE_PTR_DATA_BASE = "https://disclosures.house.gov/public_disc/ptr-pdfs"

# For bulk XML transaction data the House provides this endpoint:
# https://disclosures.house.gov/FinancialDisclosure/PressSummary → links per year
# Individual member XML: https://disclosures.house.gov/FinancialDisclosure/ViewDoc/...

# Alternative: the House Clerk API for a paginated transaction listing
HOUSE_TRANSACTIONS_URL = (
    "https://disclosures.house.gov/FinancialDisclosure/ViewMemberSearchResult"
    "?dateOfHearingFrom={from_date}&dateOfHearingTo={to_date}&filedReportType=1"
)


@retry(stop=stop_after_attempt(REQUEST_MAX_RETRIES), wait=wait_exponential(min=1, max=8))
def _get(url: str, **kwargs) -> requests.Response:
    resp = SESSION.get(url, timeout=REQUEST_TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp


def fetch_house_transactions(year: int) -> list[dict]:
    """
    Fetch all House PTR transactions for a given year.

    Strategy:
      1. Try to download the annual ZIP archive from disclosures.house.gov
      2. Parse XML files within the ZIP
      3. If ZIP unavailable, fall back to HTML scraping of search results

    Returns list of raw transaction dicts (pre-normalization).
    """
    cache_file = RAW_DIR / f"house_ptr_{year}.json"

    if USE_CACHE and cache_file.exists():
        import json
        logger.info(f"[house] Using cached data for {year}")
        with open(cache_file) as f:
            return json.load(f)

    transactions = []

    # Strategy 1: Try the known ZIP URL pattern for annual data
    try:
        transactions = _fetch_via_zip(year)
        logger.info(f"[house] Fetched {len(transactions)} transactions for {year} via ZIP")
    except Exception as e:
        logger.warning(f"[house] ZIP fetch failed for {year}: {e}")

    # Strategy 2: If ZIP failed or returned nothing, try the search form scraper
    if not transactions:
        try:
            transactions = _fetch_via_search(year)
            logger.info(f"[house] Fetched {len(transactions)} transactions for {year} via search")
        except Exception as e:
            logger.error(f"[house] Search fetch also failed for {year}: {e}")

    if transactions:
        import json
        with open(cache_file, "w") as f:
            json.dump(transactions, f)

    return transactions


def _fetch_via_zip(year: int) -> list[dict]:
    """
    Download the annual House disclosure ZIP and extract XML transaction records.
    ZIP URL pattern: https://disclosures.house.gov/public_disc/financial-pdfs/{year}FD.zip
    (This URL was valid as of 2024; if changed, the search fallback will be used.)
    """
    # Multiple known URL patterns — try each
    # PTR = Periodic Transaction Reports (STOCK Act); financial-pdfs = Annual FD (not trades)
    zip_url_patterns = [
        f"https://disclosures.house.gov/public_disc/ptr-pdfs/{year}/{year}FD.zip",
        f"https://disclosures.house.gov/public_disc/ptr-pdfs/{year}/{year}FD.ZIP",
        f"https://disclosures.house.gov/public_disc/financial-pdfs/{year}FD.zip",
    ]

    raw_dir = RAW_DIR / "house_zips"
    raw_dir.mkdir(exist_ok=True)
    local_zip = raw_dir / f"{year}FD.zip"

    zip_data = None

    for url in zip_url_patterns:
        try:
            logger.info(f"[house] Trying ZIP at {url}")
            resp = SESSION.get(url, timeout=60, stream=True)
            if resp.status_code == 200 and "application/zip" in resp.headers.get("Content-Type", ""):
                zip_data = resp.content
                with open(local_zip, "wb") as f:
                    f.write(zip_data)
                break
            elif resp.status_code == 200 and local_zip.exists():
                # URL may redirect to HTML — try local cache
                break
        except Exception as e:
            logger.debug(f"[house] ZIP URL {url} failed: {e}")
            continue

    if not zip_data and local_zip.exists():
        logger.info(f"[house] Reading local ZIP cache for {year}")
        with open(local_zip, "rb") as f:
            zip_data = f.read()

    if not zip_data:
        raise ValueError(f"Could not download ZIP for year {year}")

    return _parse_house_zip(zip_data, year)


def _parse_house_zip(zip_data: bytes, year: int) -> list[dict]:
    """Parse XML files within the House annual disclosure ZIP."""
    transactions = []

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            xml_files = [n for n in zf.namelist() if n.endswith(".xml")]
            logger.info(f"[house] ZIP contains {len(xml_files)} XML files for {year}")

            for fname in xml_files:
                try:
                    xml_bytes = zf.read(fname)
                    txns = _parse_house_xml(xml_bytes, year)
                    transactions.extend(txns)
                except Exception as e:
                    logger.debug(f"[house] Failed to parse {fname}: {e}")
    except Exception as e:
        raise ValueError(f"Could not parse ZIP: {e}")

    return transactions


def _parse_house_xml(xml_bytes: bytes, year: int) -> list[dict]:
    """
    Parse a single House member XML disclosure file.
    The XML structure varies by year; this handles the common formats.
    """
    transactions = []

    try:
        root = ET.fromstring(xml_bytes)
        ns = {"": ""}  # no namespace in most files

        # Extract filer info
        member_name = ""
        member_id = ""

        for tag in ["FilingFilerName", "MemberName", "FilerLastName"]:
            el = root.find(f".//{tag}")
            if el is not None and el.text:
                member_name = el.text.strip()
                break

        for tag in ["FilingID", "MemberID", "DocID"]:
            el = root.find(f".//{tag}")
            if el is not None and el.text:
                member_id = el.text.strip()
                break

        # Find transaction elements
        for tx_el in root.findall(".//Transaction") or root.findall(".//PeriodicTransaction"):
            txn = _parse_transaction_element(tx_el, member_name, member_id, year)
            if txn:
                transactions.append(txn)

    except ET.ParseError as e:
        logger.debug(f"[house] XML parse error: {e}")

    return transactions


def _parse_transaction_element(el: ET.Element, member_name: str, member_id: str, year: int) -> dict | None:
    """Extract fields from a single <Transaction> XML element."""
    def get(tag: str) -> str:
        child = el.find(tag)
        return (child.text or "").strip() if child is not None else ""

    asset = get("AssetName") or get("Asset") or get("Description")
    ticker = get("Ticker") or get("Symbol") or ""
    trade_type = get("Type") or get("TransactionType") or ""
    amount_code = get("Amount") or get("TransactionAmount") or ""
    tx_date = get("TransactionDate") or get("Date") or ""
    notify_date = get("NotificationDate") or get("DateDisclosed") or ""

    # Skip non-stock assets
    asset_type = get("AssetType") or "Stock"
    if any(x in asset_type.lower() for x in ["bond", "fund", "401k", "ira", "pension", "real property"]):
        # Keep ETFs and mutual funds that might have policy overlap significance
        if "etf" not in asset_type.lower() and "fund" not in asset_type.lower():
            pass  # include everything for now; filter later

    # Normalize trade type
    trade_type_norm = _normalize_trade_type(trade_type)
    if not trade_type_norm:
        return None  # Skip transfers, etc.

    # Parse amount
    amount = _parse_amount(amount_code)

    return {
        "source": "house",
        "member_name": member_name,
        "member_id": member_id,
        "asset_name": asset,
        "ticker": ticker.upper() if ticker else "",
        "trade_type": trade_type_norm,
        "raw_amount": amount_code,
        "amount_min": amount.get("min"),
        "amount_max": amount.get("max"),
        "amount_label": amount.get("label", amount_code),
        "trade_date": _normalize_date(tx_date),
        "disclosure_date": _normalize_date(notify_date),
        "asset_type": asset_type or "Stock",
        "filing_year": year,
        "source_url": HOUSE_DISCLOSURE_BASE + "/FinancialDisclosure",
    }


def _fetch_via_search(year: int) -> list[dict]:
    """
    Fallback: scrape the House search results page for a given year.
    Returns minimal data — mainly used when ZIP is unavailable.
    """
    from datetime import date
    logger.info(f"[house] Trying search scraper for {year}")
    transactions = []

    from_date = f"{year}-01-01"
    to_date   = f"{year}-12-31"

    url = (
        f"{HOUSE_DISCLOSURE_BASE}/FinancialDisclosure/ViewMemberSearchResult"
        f"?dateOfHearingFrom={from_date}&dateOfHearingTo={to_date}&filedReportType=1"
    )

    try:
        from bs4 import BeautifulSoup
        resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Parse search result table
        table = soup.find("table", {"id": "DataTables_Table_0"}) or soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")[1:]  # skip header
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            # Typical columns: Name | Office | Year | Filing
            name = cells[0].get_text(strip=True)
            # Get detail link
            link_el = cells[0].find("a") or cells[-1].find("a")
            detail_url = ""
            if link_el and link_el.get("href"):
                detail_url = HOUSE_DISCLOSURE_BASE + link_el["href"]

            transactions.append({
                "source": "house_search",
                "member_name": name,
                "filing_year": year,
                "source_url": detail_url or url,
                # Minimal data — will need detail fetch
                "ticker": "",
                "trade_type": "Unknown",
                "amount_min": None,
                "amount_max": None,
                "amount_label": "Unknown",
                "trade_date": None,
                "disclosure_date": None,
            })
    except Exception as e:
        logger.error(f"[house] Search scraper failed: {e}")

    return transactions


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



# QuiverQuantitative provides aggregated Congress trade data as a free public API.
# We use this as the primary source when the official government ZIP files are blocked.
QUIVER_BASE = "https://api.quiverquant.com/beta"
QUIVER_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _fetch_via_quiver_all() -> list[dict]:
    """Fetch Congress trades from QuiverQuantitative's free public API (both chambers)."""
    import json as _json
    cache_file = RAW_DIR / "quiver_congress_live.json"

    if USE_CACHE and cache_file.exists():
        age_hours = (datetime.now().timestamp() - cache_file.stat().st_mtime) / 3600
        if age_hours < 20:
            logger.info("[quiver] Using cached Congress trade data")
            with open(cache_file) as f:
                return _json.load(f)

    logger.info("[quiver] Fetching Congress trades from QuiverQuantitative...")
    headers = {"User-Agent": QUIVER_BROWSER_UA, "Accept": "application/json"}
    transactions = []
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
        except Exception as e:
            logger.warning(f"[quiver] {endpoint} endpoint failed: {e}")

    # Deduplicate
    seen = set()
    unique = []
    for t in transactions:
        key = (t["member_name"], t["ticker"], t["trade_date"], t["trade_type"])
        if key not in seen:
            seen.add(key)
            unique.append(t)

    logger.info(f"[quiver] Total unique transactions: {len(unique)}")
    with open(cache_file, "w") as f:
        _json.dump(unique, f)
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
        "source_url": "https://efts.senate.gov/" if source == "senate"
                      else "https://disclosures.house.gov/",
    }


def fetch_all_house(years_back: int = 5) -> list[dict]:
    """
    Fetch House PTR trade disclosures.
    Primary:  QuiverQuantitative aggregated API (works from any IP, no key required).
    Fallback: official disclosures.house.gov ZIP files.
    Returns ALL records (House + Senate); main.py resolver filters by chamber.
    """
    try:
        all_records = _fetch_via_quiver_all()
        house_records = [r for r in all_records if r.get("source") == "house"]
        if house_records:
            logger.info(f"[house] {len(house_records)} House trades via QuiverQuant")
            return all_records  # return everything; senate provider will skip if already fetched
    except Exception as e:
        logger.warning(f"[house] QuiverQuant failed: {e}")

    # Fallback to official House ZIP files
    current_year = datetime.now().year
    all_txns = []
    for year in range(current_year - years_back, current_year + 1):
        logger.info(f"[house] Fetching year {year}...")
        txns = fetch_house_transactions(year)
        all_txns.extend(txns)
        time.sleep(0.5)
    logger.info(f"[house] Total raw transactions: {len(all_txns)}")
    return all_txns
