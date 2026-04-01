"""
Generate realistic sample data for development and demo purposes.
This allows the Next.js app to run without executing the full pipeline.

Run: python scripts/seed_data.py
  or: cd pipeline && python main.py --seed

Output: data/artifacts/*.json
"""
import json
import random
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).parent.parent / "data" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

# ── Sample Data ──────────────────────────────────────────────────────────────

SAMPLE_MEMBERS = [
    {"id": "P000197", "name": "Nancy Pelosi",     "first": "Nancy",     "last": "Pelosi",     "party": "Democrat",    "chamber": "House",  "state": "CA", "policyAreas": ["Technology", "Banking / Financial Services"]},
    {"id": "B001289", "name": "Mo Brooks",        "first": "Mo",        "last": "Brooks",     "party": "Republican",  "chamber": "House",  "state": "AL", "policyAreas": ["Defense", "Industrial / Manufacturing"]},
    {"id": "B000574", "name": "Earl Blumenauer",  "first": "Earl",      "last": "Blumenauer", "party": "Democrat",    "chamber": "House",  "state": "OR", "policyAreas": ["Environment / Climate", "Transportation"]},
    {"id": "C001075", "name": "Bill Cassidy",     "first": "Bill",      "last": "Cassidy",    "party": "Republican",  "chamber": "Senate", "state": "LA", "policyAreas": ["Healthcare", "Pharmaceuticals", "Energy"]},
    {"id": "L000577", "name": "Mike Lee",         "first": "Mike",      "last": "Lee",        "party": "Republican",  "chamber": "Senate", "state": "UT", "policyAreas": ["Judiciary / Regulation", "Banking / Financial Services"]},
    {"id": "W000817", "name": "Elizabeth Warren", "first": "Elizabeth", "last": "Warren",     "party": "Democrat",    "chamber": "Senate", "state": "MA", "policyAreas": ["Banking / Financial Services", "Consumer / Retail"]},
    {"id": "S001196", "name": "Elissa Slotkin",   "first": "Elissa",    "last": "Slotkin",    "party": "Democrat",    "chamber": "House",  "state": "MI", "policyAreas": ["Defense", "Technology"]},
    {"id": "G000596", "name": "Marjorie Taylor Greene", "first": "Marjorie", "last": "Taylor Greene", "party": "Republican", "chamber": "House", "state": "GA", "policyAreas": ["Defense", "Consumer / Retail"]},
    {"id": "S000250", "name": "Pete Sessions",    "first": "Pete",      "last": "Sessions",   "party": "Republican",  "chamber": "House",  "state": "TX", "policyAreas": ["Banking / Financial Services", "Real Estate / Housing"]},
    {"id": "K000394", "name": "Andy Kim",         "first": "Andy",      "last": "Kim",        "party": "Democrat",    "chamber": "Senate", "state": "NJ", "policyAreas": ["Defense", "Technology"]},
    {"id": "C001103", "name": "Austin Scott",     "first": "Austin",    "last": "Scott",      "party": "Republican",  "chamber": "House",  "state": "GA", "policyAreas": ["Agriculture", "Defense"]},
    {"id": "D000620", "name": "John Delaney",     "first": "John",      "last": "Delaney",    "party": "Democrat",    "chamber": "House",  "state": "MD", "policyAreas": ["Banking / Financial Services", "Healthcare"]},
    {"id": "B001296", "name": "Brendan Boyle",    "first": "Brendan",   "last": "Boyle",      "party": "Democrat",    "chamber": "House",  "state": "PA", "policyAreas": ["Banking / Financial Services", "Education"]},
    {"id": "C001127", "name": "Lori Chavez-DeRemer", "first": "Lori",  "last": "Chavez-DeRemer", "party": "Republican", "chamber": "House", "state": "OR", "policyAreas": ["Healthcare", "Agriculture"]},
    {"id": "T000478", "name": "Claudia Tenney",   "first": "Claudia",   "last": "Tenney",     "party": "Republican",  "chamber": "House",  "state": "NY", "policyAreas": ["Banking / Financial Services", "Industrial / Manufacturing"]},
]

SAMPLE_COMMITTEES = [
    {"id": "SSBU",  "name": "Senate Budget Committee",                           "chamber": "Senate", "policyAreas": ["Banking / Financial Services"]},
    {"id": "SSSF",  "name": "Senate Banking, Housing, and Urban Affairs",       "chamber": "Senate", "policyAreas": ["Banking / Financial Services", "Real Estate / Housing"]},
    {"id": "SSHR",  "name": "Senate HELP Committee",                            "chamber": "Senate", "policyAreas": ["Healthcare", "Education", "Pharmaceuticals"]},
    {"id": "SSAS",  "name": "Senate Armed Services Committee",                  "chamber": "Senate", "policyAreas": ["Defense"]},
    {"id": "HSAS",  "name": "House Armed Services Committee",                   "chamber": "House",  "policyAreas": ["Defense"]},
    {"id": "HSEC",  "name": "House Energy and Commerce Committee",              "chamber": "House",  "policyAreas": ["Energy", "Healthcare", "Telecom / Media", "Technology"]},
    {"id": "HSWM",  "name": "House Ways and Means Committee",                   "chamber": "House",  "policyAreas": ["Banking / Financial Services", "Judiciary / Regulation"]},
    {"id": "HSSF",  "name": "House Financial Services Committee",               "chamber": "House",  "policyAreas": ["Banking / Financial Services"]},
    {"id": "HSAG",  "name": "House Agriculture Committee",                      "chamber": "House",  "policyAreas": ["Agriculture"]},
    {"id": "HSTI",  "name": "House Transportation and Infrastructure Committee","chamber": "House",  "policyAreas": ["Transportation", "Environment / Climate"]},
]

SAMPLE_COMPANIES = [
    {"ticker": "AAPL",  "name": "Apple Inc.",                    "sector": "Technology",        "industry": "Consumer Electronics"},
    {"ticker": "MSFT",  "name": "Microsoft Corporation",         "sector": "Technology",        "industry": "Software"},
    {"ticker": "NVDA",  "name": "NVIDIA Corporation",            "sector": "Technology",        "industry": "Semiconductors"},
    {"ticker": "JPM",   "name": "JPMorgan Chase & Co.",          "sector": "Financials",        "industry": "Banks"},
    {"ticker": "GS",    "name": "Goldman Sachs Group Inc.",      "sector": "Financials",        "industry": "Capital Markets"},
    {"ticker": "BA",    "name": "Boeing Company",                "sector": "Industrials",       "industry": "Aerospace & Defense"},
    {"ticker": "LMT",   "name": "Lockheed Martin Corporation",   "sector": "Industrials",       "industry": "Aerospace & Defense"},
    {"ticker": "RTX",   "name": "RTX Corporation",               "sector": "Industrials",       "industry": "Aerospace & Defense"},
    {"ticker": "PFE",   "name": "Pfizer Inc.",                   "sector": "Healthcare",        "industry": "Pharmaceuticals"},
    {"ticker": "JNJ",   "name": "Johnson & Johnson",             "sector": "Healthcare",        "industry": "Healthcare Products"},
    {"ticker": "MRNA",  "name": "Moderna Inc.",                  "sector": "Healthcare",        "industry": "Biotechnology"},
    {"ticker": "XOM",   "name": "Exxon Mobil Corporation",       "sector": "Energy",            "industry": "Oil & Gas"},
    {"ticker": "CVX",   "name": "Chevron Corporation",           "sector": "Energy",            "industry": "Oil & Gas"},
    {"ticker": "AMZN",  "name": "Amazon.com Inc.",               "sector": "Consumer Discretionary", "industry": "Internet Retail"},
    {"ticker": "META",  "name": "Meta Platforms Inc.",           "sector": "Communication Services", "industry": "Social Media"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.",                 "sector": "Communication Services", "industry": "Internet Services"},
    {"ticker": "V",     "name": "Visa Inc.",                     "sector": "Financials",        "industry": "Credit Services"},
    {"ticker": "UNH",   "name": "UnitedHealth Group Inc.",       "sector": "Healthcare",        "industry": "Managed Healthcare"},
    {"ticker": "NEE",   "name": "NextEra Energy Inc.",           "sector": "Utilities",         "industry": "Utilities"},
    {"ticker": "CAT",   "name": "Caterpillar Inc.",              "sector": "Industrials",       "industry": "Farm & Heavy Construction Machinery"},
]

SECTOR_TO_PA = {
    "Technology":                ["Technology", "Telecom / Media"],
    "Communication Services":    ["Telecom / Media", "Technology"],
    "Healthcare":                ["Healthcare", "Pharmaceuticals"],
    "Financials":                ["Banking / Financial Services"],
    "Industrials":               ["Industrial / Manufacturing", "Defense"],
    "Aerospace & Defense":       ["Defense", "Industrial / Manufacturing"],
    "Energy":                    ["Energy", "Environment / Climate"],
    "Utilities":                 ["Energy", "Environment / Climate"],
    "Consumer Discretionary":    ["Consumer / Retail"],
    "Consumer Staples":          ["Consumer / Retail", "Agriculture"],
    "Real Estate":               ["Real Estate / Housing"],
}

AMOUNT_RANGES = [
    {"min": 1001,    "max": 15000,   "label": "$1,001 - $15,000"},
    {"min": 15001,   "max": 50000,   "label": "$15,001 - $50,000"},
    {"min": 50001,   "max": 100000,  "label": "$50,001 - $100,000"},
    {"min": 100001,  "max": 250000,  "label": "$100,001 - $250,000"},
    {"min": 250001,  "max": 500000,  "label": "$250,001 - $500,000"},
    {"min": 500001,  "max": 1000000, "label": "$500,001 - $1,000,000"},
    {"min": 1000001, "max": 5000000, "label": "$1,000,001 - $5,000,000"},
]

TRADE_TYPES = ["Purchase", "Purchase", "Purchase", "Sale", "Sale", "Sale (Partial)"]

COMMITTEE_MEMBER_ASSIGNMENTS = {
    "P000197": ["HSEC", "HSWM"],
    "B001289": ["HSAS"],
    "B000574": ["HSTI"],
    "C001075": ["SSHR", "SSAS"],
    "L000577": ["SSSF"],
    "W000817": ["SSSF", "SSBU"],
    "S001196": ["HSAS", "HSEC"],
    "G000596": ["HSAS"],
    "S000250": ["HSSF"],
    "K000394": ["SSAS"],
    "C001103": ["HSAS", "HSAG"],
    "D000620": ["HSSF"],
    "B001296": ["HSWM", "HSSF"],
    "C001127": ["HSAG"],
    "T000478": ["HSSF", "HSWM"],
}


def _slug(name: str) -> str:
    import re
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-")))


def _make_id(*parts) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _rand_date(start_year: int = 2020) -> str:
    start = date(start_year, 1, 1)
    delta = date.today() - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")


def generate_seed_data():
    committee_map = {c["id"]: c for c in SAMPLE_COMMITTEES}
    sector_pa_map = {co["sector"]: SECTOR_TO_PA.get(co["sector"], []) for co in SAMPLE_COMPANIES}

    # ── Build members ─────────────────────────────────────────────────────
    members = []
    for raw in SAMPLE_MEMBERS:
        mid = raw["id"]
        committee_ids = COMMITTEE_MEMBER_ASSIGNMENTS.get(mid, [])
        committees = []
        for cid in committee_ids:
            c = committee_map.get(cid)
            if c:
                committees.append({
                    "id":          c["id"],
                    "name":        c["name"],
                    "role":        random.choice(["Member", "Member", "Member", "Chair", "Ranking Member"]),
                    "policy_areas": c["policyAreas"],
                })

        members.append({
            "id":               mid,
            "slug":             _slug(f"{raw['last']}-{raw['first']}"),
            "name":             raw["name"],
            "firstName":        raw["first"],
            "lastName":         raw["last"],
            "party":            raw["party"],
            "chamber":          raw["chamber"],
            "state":            raw["state"],
            "district":         str(random.randint(1, 20)) if raw["chamber"] == "House" else None,
            "photoUrl":         f"https://theunitedstates.io/images/congress/225x275/{mid}.jpg",
            "officialUrl":      f"https://www.congress.gov/member/{_slug(raw['name'])}/{mid}",
            "committees":       committees,
            "policyAreas":      raw["policyAreas"],
            "tradeCount":       0,  # filled below
            "flaggedTradeCount": 0,
            "totalValueMin":    0,
            "totalValueMax":    0,
            "performanceBadge": "Insufficient Data",
            "estimatedReturn1y": None,
            "estimatedReturn3y": None,
            "estimatedReturn5y": None,
            "performanceConfidence": "low",
            "lastDisclosureDate": None,
            "isActive":         True,
        })

    # ── Build companies ───────────────────────────────────────────────────
    companies = []
    for raw in SAMPLE_COMPANIES:
        companies.append({
            "ticker":           raw["ticker"],
            "name":             raw["name"],
            "sector":           raw["sector"],
            "industry":         raw["industry"],
            "policyAreas":      sector_pa_map.get(raw["sector"], []),
            "marketCap":        random.randint(50_000_000_000, 3_000_000_000_000),
            "tradeCount":       0,
            "flaggedTradeCount": 0,
            "uniqueTraders":    0,
            "latestTradeDate":  None,
            "buyCount":         0,
            "sellCount":        0,
        })

    # ── Generate trades ───────────────────────────────────────────────────
    trades = []
    for _ in range(800):  # 800 sample trades
        member = random.choice(members)
        company = random.choice(SAMPLE_COMPANIES)
        trade_date = _rand_date(2020)
        disc_delay = random.choices([5, 15, 30, 46, 60, 90], weights=[20, 30, 30, 10, 7, 3])[0]
        disc_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date() + timedelta(days=disc_delay)
        disc_date = disc_date_obj.strftime("%Y-%m-%d")
        if disc_date_obj > date.today():
            disc_date = date.today().strftime("%Y-%m-%d")
            disc_delay = (date.today() - datetime.strptime(trade_date, "%Y-%m-%d").date()).days

        amount = random.choices(AMOUNT_RANGES, weights=[30, 25, 20, 12, 7, 4, 2])[0]
        trade_type = random.choice(TRADE_TYPES)
        tid = _make_id(member["id"], company["ticker"], trade_date, trade_type, random.random())

        trades.append({
            "id":               tid,
            "memberId":         member["id"],
            "memberName":       member["name"],
            "memberSlug":       member["slug"],
            "memberParty":      member["party"],
            "memberChamber":    member["chamber"],
            "memberState":      member["state"],
            "ticker":           company["ticker"],
            "companyName":      company["name"],
            "sector":           company["sector"],
            "industry":         company["industry"],
            "tradeType":        trade_type,
            "tradeDate":        trade_date,
            "dateApproximate":  False,
            "disclosureDate":   disc_date,
            "disclosureDelay":  disc_delay,
            "amount":           amount,
            "assetType":        "Stock",
            "comment":          "",
            "sourceUrl":        "https://disclosures.house.gov/FinancialDisclosure",
            "isFlagged":        False,
            "flagScore":        None,
            "flagSeverity":     None,
        })

    # ── Score overlaps ────────────────────────────────────────────────────
    member_map  = {m["id"]: m for m in members}
    company_map = {co["ticker"]: co for co in companies}

    flags = []
    for trade in trades:
        member  = member_map[trade["memberId"]]
        co_data = company_map.get(trade["ticker"])
        if not co_data:
            continue

        company_pas = sector_pa_map.get(co_data["sector"], [])
        member_pas  = member["policyAreas"]
        overlap_pas = list(set(company_pas) & set(member_pas))

        # Check committee overlap
        committee_score = 0
        matched_committees = []
        for c in member.get("committees", []):
            if set(c.get("policy_areas", [])) & set(company_pas):
                committee_score = 30 if c["role"] in ("Chair", "Ranking Member") else 20
                matched_committees.append(c)

        pa_score = len(overlap_pas) * 12

        if committee_score == 0 and pa_score == 0:
            continue

        # Size score
        amt = trade["amount"]["min"]
        if amt >= 1_000_000:   size_score = 10
        elif amt >= 250_000:   size_score = 7
        elif amt >= 50_000:    size_score = 4
        elif amt >= 15_000:    size_score = 2
        else:                  size_score = 0

        # Recency
        try:
            days_ago = (date.today() - datetime.strptime(trade["tradeDate"], "%Y-%m-%d").date()).days
        except Exception:
            days_ago = 9999
        if days_ago <= 90:       recency = 10
        elif days_ago <= 365:    recency = 7
        elif days_ago <= 730:    recency = 4
        elif days_ago <= 1825:   recency = 2
        else:                    recency = 0

        # Late
        late = 5 if trade["disclosureDelay"] > 90 else (3 if trade["disclosureDelay"] > 45 else 0)

        total = min(committee_score + pa_score + size_score + recency + late, 100)

        severity = "critical" if total >= 75 else "high" if total >= 50 else "medium" if total >= 25 else "low"

        trade["isFlagged"]    = True
        trade["flagScore"]    = total
        trade["flagSeverity"] = severity

        summary_parts = []
        if matched_committees:
            summary_parts.append(f"serves on {matched_committees[0]['name']}")
        if overlap_pas:
            summary_parts.append(f"{overlap_pas[0]} policy area overlap")
        summary = f"{member['name']} traded {trade['ticker']} — {', '.join(summary_parts)} (score: {total}/100)."

        flags.append({
            "tradeId":           trade["id"],
            "memberId":          trade["memberId"],
            "memberName":        trade["memberName"],
            "memberSlug":        trade["memberSlug"],
            "ticker":            trade["ticker"],
            "companyName":       trade["companyName"],
            "tradeDate":         trade["tradeDate"],
            "tradeType":         trade["tradeType"],
            "amount":            trade["amount"],
            "overallScore":      total,
            "severity":          severity,
            "matchedPolicyAreas": overlap_pas,
            "matchedCommittees": [{"id": c["id"], "name": c["name"]} for c in matched_committees],
            "companySector":     co_data["sector"],
            "companyIndustry":   co_data["industry"],
            "factors": [
                {"factor": "Committee jurisdiction", "score": committee_score, "maxScore": 35, "explanation": f"Serves on committee with {co_data['sector']} jurisdiction"},
                {"factor": "Policy area match",      "score": pa_score,        "maxScore": 25, "explanation": f"Policy areas overlap: {', '.join(overlap_pas[:2])}"},
                {"factor": "Trade size",             "score": size_score,      "maxScore": 10, "explanation": f"Amount: {trade['amount']['label']}"},
                {"factor": "Recency",                "score": recency,         "maxScore": 10, "explanation": f"Trade reported ~{days_ago} days ago"},
            ],
            "summary": summary,
        })

    # ── Aggregate company stats ───────────────────────────────────────────
    from collections import Counter
    ticker_trades = Counter(t["ticker"] for t in trades)
    ticker_buys   = Counter(t["ticker"] for t in trades if t["tradeType"].startswith("Purchase"))
    ticker_sells  = Counter(t["ticker"] for t in trades if not t["tradeType"].startswith("Purchase"))
    ticker_traders = {tk: len({t["memberId"] for t in trades if t["ticker"] == tk}) for tk in set(t["ticker"] for t in trades)}
    ticker_flags  = Counter(f["ticker"] for f in flags)
    ticker_latest = {}
    for t in sorted(trades, key=lambda x: x["tradeDate"]):
        ticker_latest[t["ticker"]] = t["tradeDate"]

    for co in companies:
        tk = co["ticker"]
        co["tradeCount"]        = ticker_trades[tk]
        co["buyCount"]          = ticker_buys[tk]
        co["sellCount"]         = ticker_sells[tk]
        co["uniqueTraders"]     = ticker_traders.get(tk, 0)
        co["flaggedTradeCount"] = ticker_flags[tk]
        co["latestTradeDate"]   = ticker_latest.get(tk)

    # ── Aggregate member stats ────────────────────────────────────────────
    member_trade_map = {m["id"]: [t for t in trades if t["memberId"] == m["id"]] for m in members}
    member_flag_map  = {m["id"]: [f for f in flags if f["memberId"] == m["id"]] for m in members}

    sp_returns = {"2020": 16.3, "2021": 26.9, "2022": -19.4, "2023": 24.2, "2024": 23.3}
    sp_1y = 23.3

    for m in members:
        mid = m["id"]
        mtrades = member_trade_map[mid]
        mflags  = member_flag_map[mid]
        m["tradeCount"]        = len(mtrades)
        m["flaggedTradeCount"] = len(mflags)
        m["totalValueMin"]     = sum(t["amount"]["min"] for t in mtrades)
        m["totalValueMax"]     = sum(t["amount"]["max"] for t in mtrades)
        disc_dates = sorted([t["disclosureDate"] for t in mtrades if t["disclosureDate"]])
        m["lastDisclosureDate"] = disc_dates[-1] if disc_dates else None

        # Mock performance
        if len(mtrades) >= 5:
            ret_1y = round(random.gauss(sp_1y + 2, 15), 2)
            ret_3y = round(random.gauss(68 + 3, 20), 2)
            ret_5y = round(random.gauss(110 + 5, 30), 2)
            excess = ret_1y - sp_1y
            badge = ("High Outperformance" if excess >= 15 else
                     "Strong Estimated Gains" if excess >= 5 else
                     "Watchlist" if ret_1y >= 10 else
                     "Market-Tracking" if abs(excess) <= 5 else
                     "Underperforming")
            confidence = "high" if len(mtrades) >= 15 else "medium" if len(mtrades) >= 5 else "low"
        else:
            ret_1y = ret_3y = ret_5y = None
            badge = "Insufficient Data"
            confidence = "low"

        m["estimatedReturn1y"]   = ret_1y
        m["estimatedReturn3y"]   = ret_3y
        m["estimatedReturn5y"]   = ret_5y
        m["performanceBadge"]    = badge
        m["performanceConfidence"] = confidence

    # ── Performance snapshots ─────────────────────────────────────────────
    performance = []
    for m in members:
        performance.append({
            "memberId":           m["id"],
            "memberName":         m["name"],
            "memberSlug":         m["slug"],
            "estimatedReturn1y":  m["estimatedReturn1y"],
            "estimatedReturn3y":  m["estimatedReturn3y"],
            "estimatedReturn5y":  m["estimatedReturn5y"],
            "spReturn1y":         sp_1y,
            "spReturn3y":         68.0,
            "spReturn5y":         110.0,
            "excessReturn1y":     round(m["estimatedReturn1y"] - sp_1y, 2) if m["estimatedReturn1y"] else None,
            "excessReturn3y":     round(m["estimatedReturn3y"] - 68.0, 2) if m["estimatedReturn3y"] else None,
            "excessReturn5y":     round(m["estimatedReturn5y"] - 110.0, 2) if m["estimatedReturn5y"] else None,
            "confidence":         m["performanceConfidence"],
            "badge":              m["performanceBadge"],
            "tradeCount":         m["tradeCount"],
            "methodology":        "Weighted buy-and-hold simulation (seed data)",
            "caveats":            ["This is sample data for demonstration purposes only."],
        })

    # ── Dashboard ─────────────────────────────────────────────────────────
    from collections import Counter as C
    from itertools import groupby

    recent = sorted(trades, key=lambda t: t["disclosureDate"], reverse=True)[:50]

    top_traders = sorted(members, key=lambda m: m["tradeCount"], reverse=True)[:10]
    top_traders_out = [{"memberId": m["id"], "memberName": m["name"], "memberSlug": m["slug"], "tradeCount": m["tradeCount"], "party": m["party"]} for m in top_traders]

    top_performers_out = sorted([p for p in performance if p["estimatedReturn1y"] is not None], key=lambda p: p["estimatedReturn1y"], reverse=True)[:10]
    top_performers_out = [{"memberId": p["memberId"], "memberName": p["memberName"], "memberSlug": p["memberSlug"], "badge": p["badge"], "return1y": p["estimatedReturn1y"]} for p in top_performers_out]

    co_map = {co["ticker"]: co for co in companies}
    ticker_tc = C(t["ticker"] for t in trades)
    most_traded = [{"ticker": tk, "companyName": co_map.get(tk, {}).get("name", tk), "tradeCount": cnt, "sector": co_map.get(tk, {}).get("sector", "")} for tk, cnt in ticker_tc.most_common(10)]

    sector_pa_map2 = {co["sector"]: SECTOR_TO_PA.get(co["sector"], []) for co in SAMPLE_COMPANIES}
    pa_trade_map: dict = {}
    for t in trades:
        co_data = co_map.get(t["ticker"], {})
        for pa in sector_pa_map2.get(co_data.get("sector", ""), []):
            if pa not in pa_trade_map:
                pa_trade_map[pa] = {"policyArea": pa, "tradeCount": 0, "flaggedCount": 0}
            pa_trade_map[pa]["tradeCount"] += 1
    for f in flags:
        for pa in f.get("matchedPolicyAreas", []):
            if pa in pa_trade_map:
                pa_trade_map[pa]["flaggedCount"] += 1
    trades_by_pa = sorted(pa_trade_map.values(), key=lambda x: x["tradeCount"], reverse=True)

    month_map: dict = {}
    for t in trades:
        month = t["tradeDate"][:7]
        if month not in month_map:
            month_map[month] = {"month": month, "purchases": 0, "sales": 0, "total": 0}
        if t["tradeType"].startswith("Purchase"):
            month_map[month]["purchases"] += 1
        else:
            month_map[month]["sales"] += 1
        month_map[month]["total"] += 1
    activity = sorted(month_map.values(), key=lambda x: x["month"])[-24:]

    sector_map2: dict = {}
    flag_tickers = {f["ticker"] for f in flags}
    for t in trades:
        s = t["sector"]
        if s not in sector_map2:
            sector_map2[s] = {"sector": s, "count": 0, "flaggedCount": 0}
        sector_map2[s]["count"] += 1
        if t["ticker"] in flag_tickers:
            sector_map2[s]["flaggedCount"] += 1
    trades_by_sector = sorted(sector_map2.values(), key=lambda x: x["count"], reverse=True)[:12]

    dashboard = {
        "totalMembers":         len(members),
        "totalTrades":          len(trades),
        "totalFlaggedTrades":   len(flags),
        "totalCompanies":       len(companies),
        "lastUpdated":          datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recentTrades":         recent,
        "topTraders":           top_traders_out,
        "topPerformers":        top_performers_out,
        "mostTradedCompanies":  most_traded,
        "tradesByPolicyArea":   trades_by_pa,
        "activityTimeline":     activity,
        "tradesBySector":       trades_by_sector,
    }

    # ── Write artifacts ───────────────────────────────────────────────────
    for filename, data in [
        ("members.json",     members),
        ("committees.json",  SAMPLE_COMMITTEES),
        ("companies.json",   companies),
        ("trades.json",      trades),
        ("flags.json",       flags),
        ("performance.json", performance),
        ("dashboard.json",   dashboard),
        ("manifest.json", {
            "generatedAt":     datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pipelineVersion": "1.0.0-seed",
            "sources":         [{"name": "Seed data", "url": "-", "requiresKey": False, "healthy": True, "notes": "Sample data — run pipeline for real data"}],
        }),
    ]:
        path = ARTIFACTS_DIR / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Wrote {filename} ({path.stat().st_size // 1024} KB)")

    print(f"\nSeed complete: {len(members)} members · {len(trades)} trades · {len(flags)} flags · {len(companies)} companies")


if __name__ == "__main__":
    generate_seed_data()
