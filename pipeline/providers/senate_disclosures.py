"""
Senate periodic transaction report (PTR) provider.

Primary source: https://efdsearch.senate.gov/ (Electronic Financial
Disclosure search) — the old efts.senate.gov domain this file previously
used no longer resolves at all (NXDOMAIN, confirmed independent of this
project's network). efdsearch.senate.gov is the real, current domain.

That domain is protected by Akamai bot-management that returns an
unconditional 403 to this pipeline's usual hosting network — verified
identically via plain requests AND a real headless-Chromium browser
(Playwright), both blocked before ever reaching the search page with the
same generic WAF page (not a bot challenge/CAPTCHA, which is what a
fingerprint-based check would show). That points to an IP/network-range
block rather than a TLS or User-Agent fingerprint issue, so a cheap
`requests` reachability probe below is a valid proxy for whether the
heavier Playwright flow would succeed too — a genuinely-blocked run skips
installing/launching a browser entirely.

Turns out GitHub Actions' own runner network reaches this site fine (only
this project's dev environments were blocked) — two real runs got past
the reachability probe and captured screenshots + HTML dumps of the
actual pages (data/artifacts/_debug/, see _dump_debug_artifacts), which
is how the two-page flow below was verified:

1. /search/home/ is a one-time "Get Access" gate: a single #agree_statement
   checkbox whose jQuery onchange handler submits #agreement_form itself
   (confirmed from the page's own <script> block) — no separate submit
   button to click, and a first attempt that assumed the *first checkbox
   on the page* (rather than this specific id) grabbed the wrong element
   once past this gate and never got past a second bug (below) either.
2. The real Find Reports search page has a Periodic Transactions checkbox
   with report_type value 11, confirmed from the form's own HTML — its id
   is duplicated across every checkbox in the group (invalid HTML, but
   real), so it's selected by name+value instead of id/label. Its date
   fields are input#fromDate/#toDate — their name attributes
   (submitted_start_date/submitted_end_date) are not fromDate/toDate as
   an earlier guess assumed.
"""
import logging
import re
from datetime import datetime, timedelta

import requests

from pipeline.config import (
    REQUEST_TIMEOUT,
    AMOUNT_RANGES,
)

logger = logging.getLogger(__name__)

SESSION = requests.Session()

EFDSEARCH_BASE = "https://efdsearch.senate.gov"
EFDSEARCH_HOME_URL = f"{EFDSEARCH_BASE}/search/home/"

# efdsearch may block standard bot User-Agents; use a browser-like UA.
SENATE_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
SESSION.headers.update({"User-Agent": SENATE_BROWSER_UA, "Accept": "text/html"})


def fetch_all_senate(years_back: int = 5, max_reports: int = 200) -> list[dict]:
    """
    Fetch Senate PTR trade disclosures. See module docstring for why this
    probes reachability first instead of launching Playwright unconditionally.
    """
    try:
        resp = SESSION.get(EFDSEARCH_HOME_URL, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning(
                f"[senate] efdsearch.senate.gov unreachable (HTTP {resp.status_code}) — "
                f"likely Akamai bot-management blocking this network; skipping Senate this run"
            )
            return []
    except Exception as e:
        logger.warning(f"[senate] efdsearch.senate.gov unreachable ({e}) — skipping Senate this run")
        return []

    logger.info("[senate] efdsearch.senate.gov reachable — attempting live fetch via Playwright")
    try:
        return _fetch_via_efdsearch_playwright(years_back, max_reports)
    except Exception as e:
        logger.warning(f"[senate] Playwright fetch failed: {e}")
        return []


# Verified against a real captured page (see module docstring) — the
# Periodic Transactions checkbox has report_type value 11 (confirmed live
# from the form's own HTML), and its id is duplicated across every
# checkbox in the Report Types group so it can't be selected by id/label.
QPTR_CHECKBOX_SEL = "input[name='report_type'][value='11']"
QSUBMIT_SEL = "button[type='submit']"


def _dump_debug_artifacts(page, label: str) -> None:
    """Save a screenshot + HTML dump so the next run's logs show exactly
    what the real page looked like, instead of guessing selectors blind
    again. Written to data/artifacts/ so the workflow can upload them."""
    from pipeline.config import ARTIFACTS_DIR
    try:
        debug_dir = ARTIFACTS_DIR / "_debug"
        debug_dir.mkdir(exist_ok=True)
        page.screenshot(path=str(debug_dir / f"senate_{label}.png"), full_page=True)
        (debug_dir / f"senate_{label}.html").write_text(page.content())
        logger.warning(f"[senate] Debug artifacts written to data/artifacts/_debug/senate_{label}.*")
    except Exception as dump_err:
        logger.debug(f"[senate] Could not write debug artifacts: {dump_err}")


def _fetch_via_efdsearch_playwright(years_back: int, max_reports: int) -> list[dict]:
    from playwright.sync_api import sync_playwright

    from_date = (datetime.now() - timedelta(days=years_back * 365)).strftime("%m/%d/%Y")
    to_date = datetime.now().strftime("%m/%d/%Y")
    all_txns: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=SENATE_BROWSER_UA)

        try:
            page.goto(EFDSEARCH_HOME_URL, timeout=30000)
            # /search/home/ is a one-time "Get Access" gate (confirmed from a
            # captured page dump): a single #agree_statement checkbox whose
            # jQuery onchange handler does $("#agreement_form").submit(),
            # auto-navigating to the real Find Reports search page — no
            # separate submit button to click here.
            page.check("#agree_statement", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            _dump_debug_artifacts(page, "agree_page")
            browser.close()
            raise RuntimeError(f"efdsearch agreement gate failed: {e}") from e

        try:
            # Find Reports page (confirmed from a second captured dump): the
            # Periodic Transactions checkbox has report_type value 11 and a
            # non-unique id ("reportTypes" repeated on every checkbox in the
            # group — invalid HTML, but real), so it's selected by name+value
            # instead; the date fields are input#fromDate/#toDate (their name
            # attributes are submitted_start_date/submitted_end_date, not
            # fromDate/toDate as an earlier guess assumed).
            page.locator(QPTR_CHECKBOX_SEL).check(timeout=15000)
            page.fill("#fromDate", from_date)
            page.fill("#toDate", to_date)
            page.locator(QSUBMIT_SEL).click(timeout=15000)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_selector("table tbody tr", timeout=30000)
        except Exception as e:
            _dump_debug_artifacts(page, "search_page")
            browser.close()
            raise RuntimeError(f"efdsearch flow failed before reaching results: {e}") from e

        report_links = []
        for row in page.query_selector_all("table tbody tr")[:max_reports]:
            link = row.query_selector("a")
            if not link:
                continue
            href = link.get_attribute("href")
            name = row.inner_text().split("\n")[0].strip()
            if href:
                report_links.append((name, href))

        logger.info(f"[senate] Found {len(report_links)} PTR reports; fetching transaction tables")

        for name, href in report_links:
            url = href if href.startswith("http") else f"{EFDSEARCH_BASE}{href}"
            try:
                report_page = browser.new_page(user_agent=SENATE_BROWSER_UA)
                report_page.goto(url, timeout=30000)
                all_txns.extend(_parse_report_page(report_page, name, url))
                report_page.close()
            except Exception as e:
                logger.debug(f"[senate] Failed to parse report {url}: {e}")

        browser.close()

    logger.info(f"[senate] Fetched {len(all_txns)} transactions via Playwright")
    return all_txns


def _parse_report_page(page, member_name: str, report_url: str) -> list[dict]:
    """
    Parse one PTR report's transaction table. Maps columns by header text
    (rather than a fixed position) since the exact column order could not
    be verified against a live page — this self-corrects as long as the
    headers contain the expected keywords.
    """
    txns = []
    table = page.query_selector("table")
    if not table:
        return txns

    headers = [th.inner_text().strip().lower() for th in table.query_selector_all("thead th")]
    col = {}
    for i, h in enumerate(headers):
        if "transaction date" in h or h == "date":
            col.setdefault("date", i)
        elif "ticker" in h or "symbol" in h:
            col.setdefault("ticker", i)
        elif "asset" in h:
            col.setdefault("asset", i)
        elif "type" in h:
            col.setdefault("type", i)
        elif "amount" in h:
            col.setdefault("amount", i)
        elif "comment" in h:
            col.setdefault("comment", i)

    if "date" not in col or "type" not in col:
        logger.debug(f"[senate] Could not map report table headers: {headers}")
        return txns

    for tr in table.query_selector_all("tbody tr"):
        cells = [td.inner_text().strip() for td in tr.query_selector_all("td")]
        if len(cells) <= max(col.values()):
            continue

        trade_type = _normalize_type(cells[col["type"]])
        if not trade_type:
            continue

        asset = cells[col["asset"]] if "asset" in col else ""
        ticker = cells[col["ticker"]] if "ticker" in col else _extract_ticker(asset)
        amount_raw = cells[col["amount"]] if "amount" in col else ""
        amount = _parse_amount_label(amount_raw)
        tx_date = _normalize_date(cells[col["date"]])

        txns.append({
            "source": "senate",
            "member_name": member_name,
            "member_id": "",
            "asset_name": asset,
            "ticker": ticker,
            "trade_type": trade_type,
            "raw_amount": amount_raw,
            "amount_min": amount.get("min"),
            "amount_max": amount.get("max"),
            "amount_label": amount.get("label", amount_raw),
            "trade_date": tx_date,
            "disclosure_date": tx_date,
            "asset_type": "Stock",
            "comment": cells[col["comment"]] if "comment" in col else "",
            "source_url": report_url,
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
    if not asset_description:
        return ""
    patterns = [
        r"\(([A-Z]{1,5})\)",   # (AAPL)
        r"\[([A-Z]{1,5})\]",   # [MSFT]
        r"\b([A-Z]{2,5})\b",   # standalone UPPER word
    ]
    for pattern in patterns:
        match = re.search(pattern, asset_description)
        if match:
            candidate = match.group(1)
            if candidate not in {"INC", "LLC", "CORP", "LTD", "CO", "THE", "AND", "FOR", "IN", "OF"}:
                return candidate
    return ""


def _parse_amount_label(raw: str) -> dict:
    """Parse Senate amount range string to structured dict."""
    raw = (raw or "").strip()
    for _code, rng in AMOUNT_RANGES.items():
        if rng["label"].lower() == raw.lower():
            return rng
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
    raw = raw.strip().split("T")[0]
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None
