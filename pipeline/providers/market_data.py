"""
Market data provider — prices, sectors, and company info.

Primary source: Yahoo Finance via yfinance (NO API KEY REQUIRED)
  - Historical OHLC prices
  - Company sector and industry
  - Market cap

Fallback: SEC EDGAR company tickers file (NO API KEY REQUIRED)
  - ticker → company name mapping
  - CIK numbers

The yfinance library makes unofficial requests to Yahoo Finance.
It is widely used, stable, and requires no key.
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional

import requests

from pipeline.config import (
    RAW_DIR,
    USE_CACHE,
    USER_AGENT,
    SECTOR_TO_POLICY_AREAS,
)

logger = logging.getLogger(__name__)

# Lazy import yfinance to avoid hard dependency if not installed
_yf = None
def _get_yf():
    global _yf
    if _yf is None:
        import yfinance as yf
        _yf = yf
    return _yf


def get_company_info(ticker: str) -> dict:
    """
    Fetch company name, sector, and industry for a ticker symbol.
    Uses yfinance (Yahoo Finance) — no API key required.
    """
    cache_file = RAW_DIR / f"company_{ticker.upper()}.json"
    if USE_CACHE and cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)

    info = {
        "ticker": ticker.upper(),
        "name": ticker,
        "sector": "Unknown",
        "industry": "Unknown",
        "market_cap": None,
    }

    try:
        yf = _get_yf()
        stock = yf.Ticker(ticker)
        yf_info = stock.info

        info["name"]       = yf_info.get("longName") or yf_info.get("shortName") or ticker
        info["sector"]     = yf_info.get("sector", "Unknown") or "Unknown"
        info["industry"]   = yf_info.get("industry", "Unknown") or "Unknown"
        info["market_cap"] = yf_info.get("marketCap")

        time.sleep(0.2)  # gentle rate-limiting

    except Exception as e:
        logger.debug(f"[market] yfinance info failed for {ticker}: {e}")

    # Map sector to policy areas
    info["policy_areas"] = SECTOR_TO_POLICY_AREAS.get(info["sector"], [])

    with open(cache_file, "w") as f:
        json.dump(info, f)

    return info


def get_price_history(ticker: str, period: str = "5y") -> dict[str, float]:
    """
    Fetch historical closing prices for a ticker.
    Returns dict of {ISO_date: close_price}.

    Uses yfinance (Yahoo Finance, no API key).
    """
    cache_file = RAW_DIR / f"prices_{ticker.upper()}_{period}.json"
    if USE_CACHE and cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)

    prices: dict[str, float] = {}

    try:
        yf = _get_yf()
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        for date, row in hist.iterrows():
            date_str = str(date)[:10]  # YYYY-MM-DD
            prices[date_str] = float(row["Close"])
        time.sleep(0.3)

    except Exception as e:
        logger.debug(f"[market] Price history failed for {ticker}: {e}")

    with open(cache_file, "w") as f:
        json.dump(prices, f)

    return prices


def get_price_on_date(ticker: str, date: str, prices_cache: dict[str, float] | None = None) -> Optional[float]:
    """
    Get the closing price for a ticker on a specific date.
    If the exact date isn't available (weekend/holiday), use the nearest prior date.
    """
    if prices_cache is None:
        prices_cache = get_price_history(ticker)

    if not prices_cache:
        return None

    # Exact match
    if date in prices_cache:
        return prices_cache[date]

    # Find nearest prior date
    available = sorted(prices_cache.keys())
    prior = [d for d in available if d <= date]
    if prior:
        return prices_cache[prior[-1]]

    return None


def get_sp500_returns() -> dict[str, float]:
    """
    Get S&P 500 (SPY ETF) annual returns for benchmark comparison.
    Uses yfinance — no API key.
    """
    cache_file = RAW_DIR / "sp500_annual_returns.json"
    if USE_CACHE and cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)

    returns: dict[str, float] = {}

    try:
        yf = _get_yf()
        spy = yf.Ticker("SPY")
        hist = spy.history(period="10y", interval="1mo")

        # Calculate annual returns
        from datetime import datetime
        monthly = {}
        for date, row in hist.iterrows():
            ym = str(date)[:7]
            monthly[ym] = float(row["Close"])

        years = sorted(set(ym[:4] for ym in monthly.keys()))
        for year in years:
            year_months = sorted([ym for ym in monthly if ym.startswith(year)])
            if len(year_months) < 2:
                continue
            start = monthly[year_months[0]]
            end   = monthly[year_months[-1]]
            if start > 0:
                returns[year] = ((end - start) / start) * 100

    except Exception as e:
        logger.warning(f"[market] S&P 500 return fetch failed: {e}")
        # Hardcoded fallback values (approximate S&P 500 annual returns)
        returns = {
            "2019": 28.9, "2020": 16.3, "2021": 26.9,
            "2022": -19.4, "2023": 24.2, "2024": 23.3,
        }

    with open(cache_file, "w") as f:
        json.dump(returns, f)

    return returns


def get_sec_ticker_map() -> dict[str, dict]:
    """
    Download SEC EDGAR company ticker mapping.
    Official source, no API key required.
    Returns dict of {ticker: {"cik": str, "name": str}}.
    """
    cache_file = RAW_DIR / "sec_ticker_map.json"
    if USE_CACHE and cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)

    ticker_map: dict[str, dict] = {}

    try:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        resp = session.get("https://www.sec.gov/files/company_tickers.json", timeout=30)
        resp.raise_for_status()
        raw = resp.json()

        for _idx, entry in raw.items():
            ticker = entry.get("ticker", "").upper()
            if ticker:
                ticker_map[ticker] = {
                    "cik": str(entry.get("cik_str", "")),
                    "name": entry.get("title", ""),
                }
    except Exception as e:
        logger.warning(f"[market] SEC ticker map fetch failed: {e}")

    with open(cache_file, "w") as f:
        json.dump(ticker_map, f)

    logger.info(f"[market] SEC ticker map: {len(ticker_map)} companies")
    return ticker_map


def bulk_get_company_info(tickers: list[str]) -> dict[str, dict]:
    """Fetch company info for multiple tickers with progress logging."""
    results = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        if i % 50 == 0:
            logger.info(f"[market] Company info: {i}/{total}")
        results[ticker] = get_company_info(ticker)
        time.sleep(0.15)
    return results
