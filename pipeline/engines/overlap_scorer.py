"""
Policy-overlap scoring engine.

Scores each trade based on how much a member's legislative role
overlaps with the company's sector/industry.

Scoring factors (total max 100 pts):
  1. Committee jurisdiction match   35 pts
  2. Policy area match              25 pts
  3. Sector concentration           15 pts
  4. Trade size                     10 pts
  5. Recency                        10 pts
  6. Late disclosure                 5 pts

This scoring is transparent, deterministic, and reproducible.
A high score does NOT indicate wrongdoing — only potential overlap.
"""
import logging
from datetime import datetime, date

from pipeline.config import COMMITTEE_POLICY_AREAS, SECTOR_TO_POLICY_AREAS

logger = logging.getLogger(__name__)

# Severity thresholds
SEVERITY_CRITICAL = 75
SEVERITY_HIGH     = 50
SEVERITY_MEDIUM   = 25


def score_trade(
    trade: dict,
    member: dict,
    company: dict,
    all_member_trades: list[dict],
) -> dict | None:
    """
    Compute a policy-overlap score for a single trade.

    Returns a flag dict if score > 0, else None.
    """
    factors = []
    total = 0

    member_committees  = member.get("committees", [])
    member_policy_areas = member.get("policy_areas", [])
    company_sector     = company.get("sector", "")
    company_industry   = company.get("industry", "")
    company_policy_areas = company.get("policy_areas", [])

    # ── Factor 1: Committee jurisdiction match (max 35) ──────────────────
    committee_score = 0
    matched_committees = []
    for committee in member_committees:
        committee_name = committee.get("name", "")
        committee_pas  = committee.get("policy_areas", [])

        # Direct sector match via committee policy areas
        overlap = set(company_policy_areas) & set(committee_pas)
        if overlap:
            role = committee.get("role", "Member")
            # Chair/Ranking Member get extra weight
            role_bonus = 10 if role in ("Chair", "Ranking Member") else 0
            committee_score = max(committee_score, 25 + role_bonus)
            matched_committees.append(committee)

        # Also check by keyword in committee name
        for kw in ["Armed Services", "Intelligence", "Energy", "Finance", "Banking",
                   "Health", "Agriculture", "Transportation", "Technology", "Judiciary"]:
            if kw.lower() in committee_name.lower():
                # Check if this committee area matches company sector
                kw_areas = COMMITTEE_POLICY_AREAS.get(kw, [])
                if set(kw_areas) & set(company_policy_areas):
                    committee_score = max(committee_score, 20)
                    if committee not in matched_committees:
                        matched_committees.append(committee)

    committee_score = min(committee_score, 35)
    total += committee_score

    if committee_score > 0:
        factors.append({
            "factor": "Committee jurisdiction match",
            "score": committee_score,
            "maxScore": 35,
            "explanation": (
                f"Member serves on {len(matched_committees)} committee(s) with jurisdiction over "
                f"{company_sector}: {', '.join(c['name'] for c in matched_committees[:2])}"
            ),
        })

    # ── Factor 2: Policy area match (max 25) ─────────────────────────────
    pa_overlap = set(member_policy_areas) & set(company_policy_areas)
    pa_score = min(len(pa_overlap) * 12, 25) if pa_overlap else 0
    total += pa_score

    matched_pas = list(pa_overlap)
    if pa_score > 0:
        factors.append({
            "factor": "Policy area match",
            "score": pa_score,
            "maxScore": 25,
            "explanation": (
                f"Member's policy areas ({', '.join(matched_pas[:3])}) overlap with "
                f"company sector/industry ({company_sector})"
            ),
        })

    # ── Factor 3: Sector concentration (max 15) ──────────────────────────
    conc_score = 0
    if all_member_trades:
        same_sector_trades = [
            t for t in all_member_trades
            if t.get("sector") == company_sector and t.get("id") != trade.get("id")
        ]
        conc_ratio = len(same_sector_trades) / max(len(all_member_trades), 1)
        if conc_ratio >= 0.3:
            conc_score = 15
        elif conc_ratio >= 0.15:
            conc_score = 10
        elif conc_ratio >= 0.05:
            conc_score = 5

    total += conc_score
    if conc_score > 0:
        factors.append({
            "factor": "Sector concentration",
            "score": conc_score,
            "maxScore": 15,
            "explanation": (
                f"Member has made multiple trades in {company_sector} sector "
                f"({conc_score / 5:.0f}× the minimum threshold)"
            ),
        })

    # ── Factor 4: Trade size (max 10) ────────────────────────────────────
    amount_min = trade.get("amount", {}).get("min", 0)
    if amount_min >= 1_000_000:
        size_score = 10
    elif amount_min >= 250_000:
        size_score = 7
    elif amount_min >= 50_000:
        size_score = 4
    elif amount_min >= 15_000:
        size_score = 2
    else:
        size_score = 0

    total += size_score
    if size_score > 0:
        factors.append({
            "factor": "Trade size",
            "score": size_score,
            "maxScore": 10,
            "explanation": f"Estimated amount: {trade.get('amount', {}).get('label', 'unknown')}",
        })

    # ── Factor 5: Recency (max 10) ───────────────────────────────────────
    trade_date_str = trade.get("tradeDate") or trade.get("trade_date")
    recency_score = 0
    if trade_date_str:
        try:
            trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d").date()
            days_ago = (date.today() - trade_date).days
            if days_ago <= 90:
                recency_score = 10
            elif days_ago <= 365:
                recency_score = 7
            elif days_ago <= 730:
                recency_score = 4
            elif days_ago <= 1825:
                recency_score = 2
        except ValueError:
            pass

    total += recency_score
    if recency_score > 0:
        factors.append({
            "factor": "Recency",
            "score": recency_score,
            "maxScore": 10,
            "explanation": f"Trade reported recently — within {365 * (11 - recency_score):.0f} days",
        })

    # ── Factor 6: Late disclosure (max 5) ────────────────────────────────
    delay = trade.get("disclosureDelay") or trade.get("disclosure_delay_days")
    late_score = 0
    if delay is not None:
        if delay > 90:
            late_score = 5
        elif delay > 45:
            late_score = 3

    total += late_score
    if late_score > 0:
        factors.append({
            "factor": "Late disclosure",
            "score": late_score,
            "maxScore": 5,
            "explanation": f"Trade disclosed {delay} days after transaction date (STOCK Act window: 45 days)",
        })

    # ── Only flag if there's a meaningful overlap signal ─────────────────
    # At minimum, at least one core factor (committee or policy area) must fire
    has_core_signal = committee_score > 0 or pa_score > 0
    if total == 0 or not has_core_signal:
        return None

    severity = _score_to_severity(total)

    summary = _build_summary(
        member=member,
        company=company,
        matched_pas=matched_pas,
        matched_committees=matched_committees,
        total=total,
    )

    return {
        "tradeId":           trade.get("id", ""),
        "memberId":          member.get("id", ""),
        "memberName":        member.get("name", ""),
        "memberSlug":        member.get("slug", ""),
        "ticker":            company.get("ticker", ""),
        "companyName":       company.get("name", ""),
        "tradeDate":         trade_date_str or "",
        "tradeType":         trade.get("tradeType") or trade.get("trade_type", ""),
        "amount":            trade.get("amount", {"min": 1001, "max": 15000, "label": "$1,001 - $15,000"}),
        "overallScore":      min(total, 100),
        "severity":          severity,
        "matchedPolicyAreas": matched_pas,
        "matchedCommittees": [{"id": c.get("id"), "name": c.get("name")} for c in matched_committees],
        "companySector":     company_sector,
        "companyIndustry":   company_industry,
        "factors":           factors,
        "summary":           summary,
    }


def _score_to_severity(score: int) -> str:
    if score >= SEVERITY_CRITICAL: return "critical"
    if score >= SEVERITY_HIGH:     return "high"
    if score >= SEVERITY_MEDIUM:   return "medium"
    return "low"


def _build_summary(member: dict, company: dict, matched_pas: list, matched_committees: list, total: int) -> str:
    name = member.get("name", "Member")
    ticker = company.get("ticker", "")
    sector = company.get("sector", "")

    if matched_committees:
        c_name = matched_committees[0].get("name", "a relevant committee")
        return (
            f"{name} traded {ticker} ({sector}) while serving on {c_name}, "
            f"which has jurisdiction over this sector (score: {total}/100)."
        )
    if matched_pas:
        pa = matched_pas[0]
        return (
            f"{name} traded {ticker} ({sector}), which overlaps with their "
            f"{pa} policy area focus (score: {total}/100)."
        )
    return (
        f"{name} traded {ticker} ({sector}), a sector connected to their legislative focus "
        f"(score: {total}/100)."
    )
