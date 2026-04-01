"""
Congress member and committee data provider.

Primary source: unitedstates/congress-legislators (GitHub, public domain)
  https://unitedstates.github.io/congress-legislators/legislators-current.json
  https://unitedstates.github.io/congress-legislators/legislators-historical.json
  https://unitedstates.github.io/congress-legislators/committees-current.json
  https://unitedstates.github.io/congress-legislators/committee-membership-current.json

No API key required. These files are maintained by a civic community and are
public domain. Updated very frequently (multiple times per day).

Optional enrichment (congress.gov API, free key):
  If CONGRESS_API_KEY is set, fetch additional metadata like photos and
  more detailed committee data.
"""
import json
import logging
import time
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from pipeline.config import (
    UNITEDSTATES_MEMBERS_URL,
    UNITEDSTATES_HISTORICAL_URL,
    UNITEDSTATES_COMMITTEES_URL,
    UNITEDSTATES_COMMITTEE_MEMBERSHIP_URL,
    RAW_DIR,
    REQUEST_TIMEOUT,
    USER_AGENT,
    USE_CACHE,
    CONGRESS_API_KEY,
    COMMITTEE_POLICY_AREAS,
)

logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
def _get_json(url: str) -> list | dict:
    resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _cache_get(key: str) -> list | dict | None:
    f = RAW_DIR / f"{key}.json"
    if USE_CACHE and f.exists():
        with open(f) as fp:
            return json.load(fp)
    return None


def _cache_set(key: str, data: list | dict) -> None:
    f = RAW_DIR / f"{key}.json"
    with open(f, "w") as fp:
        json.dump(data, fp)


def fetch_current_members() -> list[dict]:
    """Fetch all current members of Congress from unitedstates project."""
    cached = _cache_get("legislators_current")
    if cached is not None:
        return cached
    logger.info("[members] Fetching current legislators from unitedstates.io")
    data = _get_json(UNITEDSTATES_MEMBERS_URL)
    _cache_set("legislators_current", data)
    return data


def fetch_historical_members() -> list[dict]:
    """Fetch all historical members (for past trades)."""
    cached = _cache_get("legislators_historical")
    if cached is not None:
        return cached
    logger.info("[members] Fetching historical legislators from unitedstates.io")
    data = _get_json(UNITEDSTATES_HISTORICAL_URL)
    _cache_set("legislators_historical", data)
    return data


def fetch_committees() -> list[dict]:
    """Fetch current committee data."""
    cached = _cache_get("committees_current")
    if cached is not None:
        return cached
    logger.info("[committees] Fetching committee data from unitedstates.io")
    data = _get_json(UNITEDSTATES_COMMITTEES_URL)
    _cache_set("committees_current", data)
    return data


def fetch_committee_membership() -> dict:
    """Fetch committee membership mapping {committee_id: [member_ids]}."""
    cached = _cache_get("committee_membership")
    if cached is not None:
        return cached
    logger.info("[committees] Fetching committee membership from unitedstates.io")
    data = _get_json(UNITEDSTATES_COMMITTEE_MEMBERSHIP_URL)
    _cache_set("committee_membership", data)
    return data


def normalize_members(raw_members: list[dict]) -> list[dict]:
    """
    Normalize the unitedstates legislator JSON into our Member schema.
    """
    members = []

    for raw in raw_members:
        try:
            bio = raw.get("id", {})
            name_data = raw.get("name", {})
            bio_guide_id = bio.get("bioguide", "")
            if not bio_guide_id:
                continue

            terms = raw.get("terms", [])
            if not terms:
                continue

            # Use the most recent term
            latest_term = terms[-1]
            chamber_raw = latest_term.get("type", "")
            chamber = "House" if chamber_raw == "rep" else "Senate"
            state = latest_term.get("state", "")
            party_raw = latest_term.get("party", "")
            party = _normalize_party(party_raw)

            first_name = name_data.get("first", "")
            last_name  = name_data.get("last", "")
            full_name  = name_data.get("official_full", f"{first_name} {last_name}").strip()

            # Slug: "lastname-firstname"
            slug = _slugify(f"{last_name}-{first_name}")

            # Photo URL from unitedstates bioguide convention
            photo_url = f"https://theunitedstates.io/images/congress/225x275/{bio_guide_id}.jpg"

            # Official website
            official_url = latest_term.get("url", "")

            members.append({
                "id": bio_guide_id,
                "slug": slug,
                "name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "party": party,
                "chamber": chamber,
                "state": state,
                "district": str(latest_term.get("district", "")) if chamber == "House" else None,
                "photo_url": photo_url,
                "official_url": official_url,
                "bioguide_id": bio_guide_id,
                "thomas_id": bio.get("thomas", ""),
                "is_active": True,
            })

        except Exception as e:
            logger.debug(f"[members] Skipped member due to error: {e}")

    logger.info(f"[members] Normalized {len(members)} members")
    return members


def normalize_committees(raw_committees: list[dict], membership: dict) -> list[dict]:
    """
    Normalize committee data and annotate with policy areas.
    """
    committees = []

    for raw in raw_committees:
        committee_id   = raw.get("thomas_id", "") or raw.get("committee_id", "")
        name           = raw.get("name", "")
        chamber_raw    = raw.get("type", "")
        chamber        = "House" if chamber_raw == "house" else "Senate"

        # Find matching policy areas by keyword matching against committee name
        policy_areas = []
        for kw, areas in COMMITTEE_POLICY_AREAS.items():
            if kw.lower() in name.lower():
                policy_areas.extend(areas)

        # Remove duplicates while preserving order
        seen = set()
        policy_areas_dedup = []
        for pa in policy_areas:
            if pa not in seen:
                policy_areas_dedup.append(pa)
                seen.add(pa)

        # Get member IDs from membership data
        member_ids = []
        if committee_id in membership:
            for member_rec in membership[committee_id]:
                if isinstance(member_rec, dict):
                    bioguide = member_rec.get("bioguide_id", "")
                    if bioguide:
                        member_ids.append(bioguide)

        committees.append({
            "id": committee_id,
            "name": name,
            "chamber": chamber,
            "policy_areas": policy_areas_dedup,
            "member_ids": member_ids,
        })

        # Also process subcommittees
        for sub in raw.get("subcommittees", []):
            sub_id = f"{committee_id}{sub.get('thomas_id', '')}"
            sub_name = sub.get("name", "")
            sub_members = []
            if sub_id in membership:
                for rec in membership[sub_id]:
                    if isinstance(rec, dict):
                        bg = rec.get("bioguide_id", "")
                        if bg:
                            sub_members.append(bg)

            sub_policy_areas = list(policy_areas_dedup)  # inherit from parent

            committees.append({
                "id": sub_id,
                "name": f"{name} — {sub_name}",
                "chamber": chamber,
                "policy_areas": sub_policy_areas,
                "member_ids": sub_members,
                "parent_id": committee_id,
            })

    logger.info(f"[committees] Normalized {len(committees)} committees/subcommittees")
    return committees


def build_member_committee_map(
    members: list[dict],
    committees: list[dict],
) -> dict[str, list[dict]]:
    """
    Build a map from member_id → list of committee refs with roles.
    """
    # membership dict: member_id → [committee_ids]
    member_to_committees: dict[str, list[dict]] = {m["id"]: [] for m in members}

    for committee in committees:
        for member_id in committee.get("member_ids", []):
            if member_id in member_to_committees:
                member_to_committees[member_id].append({
                    "id": committee["id"],
                    "name": committee["name"],
                    "role": "Member",  # role data not always available in bulk data
                    "policy_areas": committee.get("policy_areas", []),
                })

    return member_to_committees


def _normalize_party(raw: str) -> str:
    raw_l = (raw or "").lower()
    if "democrat" in raw_l or raw_l == "d":
        return "Democrat"
    if "republican" in raw_l or raw_l == "r":
        return "Republican"
    if "independent" in raw_l or raw_l == "i":
        return "Independent"
    return "Other"


def _slugify(name: str) -> str:
    import re
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-")))
