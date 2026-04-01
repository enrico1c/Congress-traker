"""
Central configuration for the Congress Trades data pipeline.
All constants, paths, and provider settings are here.
"""
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR       = Path(__file__).parent.parent
DATA_DIR       = ROOT_DIR / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
ARTIFACTS_DIR  = DATA_DIR / "artifacts"

for _d in (RAW_DIR, PROCESSED_DIR, ARTIFACTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Optional API keys (loaded from env; never required) ──────────────────
# congress.gov: get free key at https://api.congress.gov/sign-up
CONGRESS_API_KEY   = os.getenv("CONGRESS_API_KEY", "")
# Alpha Vantage (price data fallback): https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_KEY  = os.getenv("ALPHA_VANTAGE_KEY", "")
# Quiver Quantitative (NO LONGER FREE — skip unless user provides key)
QUIVER_API_KEY     = os.getenv("QUIVER_QUANT_API_KEY", "")

# ── Primary data sources (NO KEY REQUIRED) ────────────────────────────────

# House STOCK Act Periodic Transaction Reports
# Official downloadable ZIP files per year — absolutely no key needed
HOUSE_DISCLOSURE_BASE   = "https://disclosures.house.gov"
HOUSE_DISCLOSURE_SEARCH = "https://disclosures.house.gov/FinancialDisclosure/ViewMemberSearchResult"
# Annual data file pattern (XML per member, or summary CSV):
# https://disclosures.house.gov/FinancialDisclosure/PressSummary?year=YYYY
HOUSE_DATA_URL_TEMPLATE = "https://disclosures.house.gov/FinancialDisclosure/PressSummary?year={year}"

# Senate EFTS — public JSON API, no key
SENATE_EFTS_BASE = "https://efts.senate.gov/LATEST/search-index"
SENATE_EFTS_PARAMS = {
    "q": "",
    "dateRange": "custom",
    "fromDate": "2012-01-01",
    "toDate":   "",   # filled at runtime
    "pageSize": 100,
    "offset":   0,
}

# unitedstates/congress — public GitHub raw JSON (public domain data)
UNITEDSTATES_MEMBERS_URL   = "https://unitedstates.github.io/congress-legislators/legislators-current.json"
UNITEDSTATES_HISTORICAL_URL = "https://unitedstates.github.io/congress-legislators/legislators-historical.json"
UNITEDSTATES_COMMITTEES_URL = "https://unitedstates.github.io/congress-legislators/committees-current.json"
UNITEDSTATES_COMMITTEE_MEMBERSHIP_URL = "https://unitedstates.github.io/congress-legislators/committee-membership-current.json"

# SEC EDGAR company search (no key, official API)
SEC_EDGAR_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index?q=\"{ticker}\"&dateRange=custom&startdt=2020-01-01&forms=10-K"
SEC_EDGAR_TICKER_MAP     = "https://www.sec.gov/files/company_tickers.json"

# ── Pipeline settings ─────────────────────────────────────────────────────
YEARS_BACK      = int(os.getenv("PIPELINE_YEARS_BACK", "5"))
USE_CACHE       = os.getenv("PIPELINE_USE_CACHE", "true").lower() == "true"
LOG_LEVEL       = os.getenv("PIPELINE_LOG_LEVEL", "INFO")
PIPELINE_VERSION = "1.0.0"

# HTTP settings
REQUEST_TIMEOUT     = 30   # seconds
REQUEST_MAX_RETRIES = 3
REQUEST_RETRY_WAIT  = 2    # seconds between retries
USER_AGENT = (
    "CongressTrades-Pipeline/1.0 "
    "(public-data transparency tool; "
    "https://github.com/your-username/congress-trades)"
)

# ── Amount range map ─────────────────────────────────────────────────────
# STOCK Act uses standardized value ranges
AMOUNT_RANGES = {
    "1":  {"min": 1001,        "max": 15000,       "label": "$1,001 - $15,000"},
    "2":  {"min": 15001,       "max": 50000,        "label": "$15,001 - $50,000"},
    "3":  {"min": 50001,       "max": 100000,       "label": "$50,001 - $100,000"},
    "4":  {"min": 100001,      "max": 250000,       "label": "$100,001 - $250,000"},
    "5":  {"min": 250001,      "max": 500000,       "label": "$250,001 - $500,000"},
    "6":  {"min": 500001,      "max": 1000000,      "label": "$500,001 - $1,000,000"},
    "7":  {"min": 1000001,     "max": 5000000,      "label": "$1,000,001 - $5,000,000"},
    "8":  {"min": 5000001,     "max": 25000000,     "label": "$5,000,001 - $25,000,000"},
    "9":  {"min": 25000001,    "max": 50000000,     "label": "$25,000,001 - $50,000,000"},
    "10": {"min": 50000001,    "max": 100000000,    "label": "$50,000,001 - $100,000,000"},
    "11": {"min": 100000001,   "max": 1000000000,   "label": "Over $100,000,000"},
    # House-specific labels
    "SP": {"min": 1001,        "max": 15000,        "label": "$1,001 - $15,000"},
    "SN": {"min": 1001,        "max": 15000,        "label": "$1,001 - $15,000"},
}

# Parse dollar range strings like "$15,001 - $50,000"
AMOUNT_LABEL_MAP = {v["label"]: v for v in AMOUNT_RANGES.values()}

# ── Sector → Policy Area mapping ─────────────────────────────────────────
SECTOR_TO_POLICY_AREAS: dict[str, list[str]] = {
    "Technology":                  ["Technology", "Telecom / Media"],
    "Communication Services":      ["Telecom / Media", "Technology"],
    "Healthcare":                  ["Healthcare", "Pharmaceuticals"],
    "Health Care":                 ["Healthcare", "Pharmaceuticals"],
    "Pharmaceuticals":             ["Pharmaceuticals", "Healthcare"],
    "Biotechnology":               ["Pharmaceuticals", "Healthcare"],
    "Energy":                      ["Energy", "Environment / Climate"],
    "Utilities":                   ["Energy", "Environment / Climate"],
    "Financials":                  ["Banking / Financial Services"],
    "Financial Services":          ["Banking / Financial Services"],
    "Banks":                       ["Banking / Financial Services"],
    "Insurance":                   ["Banking / Financial Services"],
    "Industrials":                 ["Industrial / Manufacturing", "Defense"],
    "Aerospace & Defense":         ["Defense", "Industrial / Manufacturing"],
    "Defense & Aerospace":         ["Defense", "Industrial / Manufacturing"],
    "Consumer Discretionary":      ["Consumer / Retail"],
    "Consumer Staples":            ["Consumer / Retail", "Agriculture"],
    "Real Estate":                 ["Real Estate / Housing"],
    "Materials":                   ["Industrial / Manufacturing", "Environment / Climate"],
    "Transportation":              ["Transportation"],
    "Agriculture":                 ["Agriculture"],
    "Education":                   ["Education"],
}

# ── Committee → Policy Area mapping ─────────────────────────────────────
COMMITTEE_POLICY_AREAS: dict[str, list[str]] = {
    # House committees
    "Armed Services":              ["Defense"],
    "Intelligence":                ["Defense", "Technology"],
    "Homeland Security":           ["Defense"],
    "Energy and Commerce":         ["Energy", "Healthcare", "Telecom / Media", "Technology"],
    "Ways and Means":              ["Banking / Financial Services", "Judiciary / Regulation"],
    "Financial Services":          ["Banking / Financial Services"],
    "Agriculture":                 ["Agriculture"],
    "Transportation and Infrastructure": ["Transportation", "Environment / Climate"],
    "Science, Space, and Technology":    ["Technology"],
    "Education and the Workforce":       ["Education"],
    "Natural Resources":                 ["Energy", "Environment / Climate"],
    "Judiciary":                         ["Judiciary / Regulation"],
    "Appropriations":                    ["Banking / Financial Services"],
    "Budget":                            ["Banking / Financial Services"],
    "Foreign Affairs":                   ["Defense"],
    "Oversight and Accountability":      ["Judiciary / Regulation"],
    # Senate committees
    "Banking, Housing, and Urban Affairs": ["Banking / Financial Services", "Real Estate / Housing"],
    "Finance":                            ["Banking / Financial Services"],
    "Armed Services":                     ["Defense"],
    "Commerce, Science, and Transportation": ["Telecom / Media", "Technology", "Transportation"],
    "Health, Education, Labor, and Pensions": ["Healthcare", "Education", "Pharmaceuticals"],
    "Environment and Public Works":       ["Environment / Climate", "Transportation"],
    "Agriculture, Nutrition, and Forestry": ["Agriculture"],
    "Energy and Natural Resources":       ["Energy", "Environment / Climate"],
    "Intelligence":                       ["Defense", "Technology"],
    "Foreign Relations":                  ["Defense"],
    "Judiciary":                          ["Judiciary / Regulation"],
}
