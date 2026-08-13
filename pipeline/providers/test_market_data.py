"""
Regression check for _safe_filename_component() (pipeline/providers/market_data.py).

Root cause: get_company_info()/get_price_history() built cache file paths
directly from ticker strings. Some tickers legitimately contain '/'
(e.g. BRK/A), and unresolved-ticker fallbacks can contain arbitrary
truncated-asset-name characters (e.g. "Pandora A/S"[:10] == "PANDORA A/").
Either way, '/' in the string was interpreted as a path separator, so
open(cache_file, "w") raised FileNotFoundError for a non-existent
subdirectory and crashed the whole "Update Trade Data" pipeline run.

Run: python pipeline/providers/test_market_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # repo root, same trick main.py uses

from pipeline.providers.market_data import _safe_filename_component


def test_safe_filename_component_strips_path_separators():
    assert _safe_filename_component("PANDORA A/") == "PANDORA_A_"
    assert _safe_filename_component("BRK/A") == "BRK_A"
    assert _safe_filename_component("AAPL") == "AAPL"
    assert "/" not in _safe_filename_component("A/B/C")
    assert "\\" not in _safe_filename_component("A\\B")


if __name__ == "__main__":
    test_safe_filename_component_strips_path_separators()
    print("ok")
