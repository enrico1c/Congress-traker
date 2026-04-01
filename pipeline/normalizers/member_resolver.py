"""
Resolve raw member names from trade disclosures to canonical member records.
Uses fuzzy string matching (rapidfuzz) to handle name variations.
"""
import logging
import re
from rapidfuzz import fuzz, process as fuzz_process

logger = logging.getLogger(__name__)

# Min score for a fuzzy match to be accepted
FUZZY_THRESHOLD = 80


class MemberResolver:
    """
    Resolves disclosure member names → canonical member IDs.

    Builds an index of (last_name, first_name, state, chamber) tuples
    from the canonical member list and fuzzy-matches incoming names.
    """

    def __init__(self, canonical_members: list[dict]):
        self.members = canonical_members
        self._build_index()

    def _build_index(self):
        self._by_id    = {m["id"]: m for m in self.members}
        self._names    = [(m["name"].lower(), m["id"]) for m in self.members]
        self._last_names = {}
        for m in self.members:
            last = m.get("last_name", "").lower()
            if last:
                self._last_names.setdefault(last, []).append(m)

    def resolve(self, name: str, state: str = "", chamber: str = "") -> dict | None:
        """
        Resolve a display name to a canonical member.
        Returns the member dict or None if unresolvable.
        """
        if not name:
            return None

        name_clean = _normalize_name(name)

        # Try exact match first
        for m in self.members:
            if m["name"].lower() == name_clean.lower():
                return m

        # Try last name match (faster)
        last = name_clean.split()[-1].lower() if name_clean.split() else ""
        candidates = self._last_names.get(last, [])

        if candidates:
            # Filter by chamber / state if available
            if chamber:
                ch_norm = "House" if "house" in chamber.lower() or chamber.lower() == "rep" else "Senate"
                filtered = [c for c in candidates if c.get("chamber") == ch_norm]
                if filtered:
                    candidates = filtered
            if state:
                filtered = [c for c in candidates if c.get("state") == state.upper()]
                if filtered:
                    candidates = filtered

            if len(candidates) == 1:
                return candidates[0]

        # Fuzzy match against all names
        all_names = [m["name"] for m in self.members]
        result = fuzz_process.extractOne(
            name_clean,
            all_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=FUZZY_THRESHOLD,
        )
        if result:
            matched_name, score, _idx = result
            for m in self.members:
                if m["name"] == matched_name:
                    logger.debug(f"[resolver] '{name}' → '{matched_name}' (score={score})")
                    return m

        logger.debug(f"[resolver] Could not resolve: '{name}'")
        return None

    def get_by_id(self, member_id: str) -> dict | None:
        return self._by_id.get(member_id)


def _normalize_name(name: str) -> str:
    """Normalize a member name for comparison."""
    # Remove titles, suffixes
    name = re.sub(r"\b(Hon\.|Dr\.|Mr\.|Mrs\.|Ms\.|Jr\.|Sr\.|II|III|IV)\b", "", name, flags=re.IGNORECASE)
    # Normalize spaces
    name = " ".join(name.split())
    return name.strip()
