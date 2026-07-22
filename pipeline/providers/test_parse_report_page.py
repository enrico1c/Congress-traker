"""
Regression check for _parse_report_page() (pipeline/providers/senate_disclosures.py).

Runs against a SYNTHETIC fixture (fixtures/synthetic_report_page.html) — NOT
a real captured Senate eFD page. efdsearch.senate.gov is Akamai-blocked from
every environment available when this test was written, so there is no real
page to verify against yet. The fixture encodes a hypothesis (see its own
header comment) about why the parser returned 0/25 transactions in
production: a "Filer Information" table renders before the real transactions
table, and the old code grabbed the first <table> unconditionally.

This only proves the fixed table-selection logic behaves as designed against
that hypothesis — it does NOT prove the hypothesis matches the real page.
Replace the fixture with a real captured report (see the new
"report_page_empty" debug dump in senate_disclosures.py) and re-run this
before trusting the fix against production data.

Run: python pipeline/providers/test_parse_report_page.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root, same trick main.py uses

from playwright.sync_api import sync_playwright

from pipeline.providers.senate_disclosures import _parse_report_page

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_report_page.html"


def test_parse_report_page_skips_filer_info_table():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(FIXTURE.as_uri())
        txns = _parse_report_page(page, "Jane Q. Senator", str(FIXTURE))
        browser.close()

    assert len(txns) == 2, f"expected 2 transactions, got {len(txns)}: {txns}"

    first = txns[0]
    assert first["ticker"] == "AAPL"
    assert first["trade_type"] == "Purchase"
    assert first["trade_date"] == "2026-01-15"
    assert first["amount_min"] == 1001 and first["amount_max"] == 15000

    second = txns[1]
    assert second["ticker"] == "MSFT"
    assert second["trade_type"] == "Sale"
    assert second["comment"] == "Routine rebalancing"

    print("PASS: _parse_report_page skipped the Filer Information table and parsed 2 transactions")


if __name__ == "__main__":
    test_parse_report_page_skips_filer_info_table()
