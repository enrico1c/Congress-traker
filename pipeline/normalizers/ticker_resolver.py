"""
Resolve asset descriptions from disclosures to canonical ticker symbols.

Strategy:
1. If a ticker is already extracted, validate it against the SEC ticker map
2. If no ticker, extract it from the asset description using pattern matching
3. If still unresolved, try fuzzy company name matching against SEC data
"""
import logging
import re
from rapidfuzz import fuzz, process as fuzz_process

logger = logging.getLogger(__name__)


class TickerResolver:
    def __init__(self, sec_ticker_map: dict[str, dict]):
        """
        sec_ticker_map: {ticker_symbol: {"name": str, "cik": str}}
        """
        self.ticker_map = sec_ticker_map
        self._valid_tickers = set(sec_ticker_map.keys())
        # Build reverse name → ticker map for fuzzy matching
        self._names_index = [(v["name"].lower(), k) for k, v in sec_ticker_map.items() if v.get("name")]

    def resolve(self, ticker: str, asset_description: str) -> str:
        """
        Returns validated/resolved ticker symbol or empty string.
        """
        # Strategy 1: Validate existing ticker
        if ticker and ticker.upper() in self._valid_tickers:
            return ticker.upper()

        # Strategy 2: Try to extract ticker from description
        if asset_description:
            extracted = _extract_ticker_from_text(asset_description)
            if extracted and extracted in self._valid_tickers:
                return extracted

        # Strategy 3: Fuzzy match company name
        if asset_description:
            resolved = self._fuzzy_match_name(asset_description)
            if resolved:
                logger.debug(f"[ticker] Fuzzy resolved '{asset_description}' → {resolved}")
                return resolved

        # Return original ticker even if unvalidated (some legit tickers are newly listed)
        if ticker and re.match(r"^[A-Z]{1,5}$", ticker.upper()):
            return ticker.upper()

        return ""

    def _fuzzy_match_name(self, description: str, threshold: int = 80) -> str:
        """Fuzzy-match company name to SEC-registered ticker."""
        # Clean description
        clean = re.sub(r"\(.*?\)|\[.*?\]", "", description).strip()
        clean = re.sub(r"\b(Inc|Corp|Ltd|LLC|Co|Group|Holdings|Common Stock|Class [AB])\b", "", clean, flags=re.IGNORECASE).strip()
        if len(clean) < 3:
            return ""

        result = fuzz_process.extractOne(
            clean.lower(),
            [n for n, _ in self._names_index],
            scorer=fuzz.token_set_ratio,
            score_cutoff=threshold,
        )
        if result:
            matched_name, score, idx = result
            return self._names_index[idx][1]  # Return ticker
        return ""


def _extract_ticker_from_text(text: str) -> str:
    """Extract potential ticker from text using regex patterns."""
    # Parenthetical ticker: "Apple Inc. (AAPL)"
    m = re.search(r"\b([A-Z]{1,5})\b\s*\)", text)
    if m:
        return m.group(1)

    # Pattern: word in parens
    m = re.search(r"\(([A-Z]{2,5})\)", text)
    if m:
        return m.group(1)

    # Standalone all-caps word 2-5 letters surrounded by non-word
    candidates = re.findall(r"\b([A-Z]{2,5})\b", text)
    stopwords = {"INC", "LLC", "CORP", "LTD", "THE", "AND", "FOR", "IN", "OF", "CO", "ETF", "FUND", "REIT", "COM"}
    for c in candidates:
        if c not in stopwords:
            return c

    return ""
