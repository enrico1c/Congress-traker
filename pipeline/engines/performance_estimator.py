"""
Portfolio performance estimation engine.

Uses disclosed trade data + Yahoo Finance historical prices to
reconstruct estimated portfolio returns.

METHODOLOGY (transparent):
  1. For each Purchase: record entry price on trade date
  2. For each Sale:     record exit price on trade date
  3. Compute simple return per position: (exit - entry) / entry
  4. Weight by midpoint of reported amount range
  5. Aggregate weighted returns for 1Y, 3Y, 5Y windows
  6. Compare against S&P 500 (SPY) as benchmark
  7. Assign confidence based on trade count and data quality

IMPORTANT CAVEATS (surfaced to the UI):
  - Only disclosed transactions captured — not full portfolio
  - Value ranges (not exact amounts) create significant uncertainty
  - Disclosure delay means exact entry/exit prices are approximate
  - Tax treatment, dividends, and fees not modeled
  - Members may have large unreported legacy holdings
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Confidence thresholds
HIGH_CONFIDENCE_MIN_TRADES = 15
MED_CONFIDENCE_MIN_TRADES  = 5

# Performance badge thresholds (excess return vs S&P over 1Y)
BADGE_HIGH_OUTPERFORM  = 15.0   # 15%+ above S&P
BADGE_STRONG_GAINS     = 5.0    # 5%+ above S&P
BADGE_WATCHLIST        = 10.0   # 10%+ absolute return regardless
BADGE_MARKET_TRACKING  = 5.0    # within 5% of S&P
BADGE_UNDERPERFORMING  = -10.0  # 10%+ below S&P


def estimate_member_performance(
    member: dict,
    trades: list[dict],
    price_histories: dict[str, dict[str, float]],
    sp500_returns: dict[str, float],
) -> dict:
    """
    Estimate portfolio performance for a single member.

    Args:
        member:          Canonical member dict
        trades:          List of trade dicts for this member
        price_histories: {ticker: {date: price}} for all relevant tickers
        sp500_returns:   {year: annual_return_pct}

    Returns performance snapshot dict.
    """
    today = date.today()
    caveats = [
        "Estimates are based on disclosed transactions only — actual portfolio holdings not captured.",
        "Value ranges (not exact amounts) used for position sizing — creates substantial uncertainty.",
        "Trades disclosed up to 45 days late — entry/exit prices may differ from reported dates.",
    ]

    if not trades:
        return _empty_snapshot(member, "Insufficient Data", caveats)

    # Filter to equity trades only
    equity_trades = [
        t for t in trades
        if t.get("assetType", "Stock") in ("Stock", "Option", "ETF", "Common Stock")
        and t.get("ticker")
        and t.get("tradeDate")
    ]

    if len(equity_trades) < 3:
        return _empty_snapshot(member, "Insufficient Data", caveats)

    # Calculate returns for different windows
    def calc_window_return(years: int) -> Optional[float]:
        cutoff = today - timedelta(days=years * 365)
        window_trades = [
            t for t in equity_trades
            if t.get("tradeDate") and _parse_date(t["tradeDate"]) >= cutoff
        ]
        if len(window_trades) < 2:
            return None
        return _compute_weighted_return(window_trades, price_histories, today, years)

    ret_1y = calc_window_return(1)
    ret_3y = calc_window_return(3)
    ret_5y = calc_window_return(5)

    # S&P 500 benchmark returns for windows
    sp_1y = _get_sp_window_return(sp500_returns, 1)
    sp_3y = _get_sp_window_return(sp500_returns, 3)
    sp_5y = _get_sp_window_return(sp500_returns, 5)

    excess_1y = (ret_1y - sp_1y) if ret_1y is not None and sp_1y is not None else None
    excess_3y = (ret_3y - sp_3y) if ret_3y is not None and sp_3y is not None else None
    excess_5y = (ret_5y - sp_5y) if ret_5y is not None and sp_5y is not None else None

    # Determine confidence
    if len(equity_trades) >= HIGH_CONFIDENCE_MIN_TRADES:
        confidence = "high"
    elif len(equity_trades) >= MED_CONFIDENCE_MIN_TRADES:
        confidence = "medium"
    else:
        confidence = "low"

    # Assign badge
    badge = _assign_badge(ret_1y, excess_1y)

    return {
        "memberId":          member["id"],
        "memberName":        member["name"],
        "memberSlug":        member["slug"],
        "estimatedReturn1y": _round(ret_1y),
        "estimatedReturn3y": _round(ret_3y),
        "estimatedReturn5y": _round(ret_5y),
        "spReturn1y":        _round(sp_1y),
        "spReturn3y":        _round(sp_3y),
        "spReturn5y":        _round(sp_5y),
        "excessReturn1y":    _round(excess_1y),
        "excessReturn3y":    _round(excess_3y),
        "excessReturn5y":    _round(excess_5y),
        "confidence":        confidence,
        "badge":             badge,
        "tradeCount":        len(equity_trades),
        "methodology":       "Weighted buy-and-hold with midpoint value ranges and Yahoo Finance prices",
        "caveats":           caveats,
    }


def _compute_weighted_return(
    trades: list[dict],
    price_histories: dict[str, dict[str, float]],
    today: date,
    window_years: int,
) -> Optional[float]:
    """
    Compute a simple weighted return across a set of trades.
    Each purchase creates a position; each sale closes one.
    Open positions are valued at today's price.
    """
    total_weight   = 0.0
    weighted_return = 0.0
    cutoff = today - timedelta(days=window_years * 365)

    # Simple approach: for each purchase, compute return to today or to the matching sale
    purchases = [t for t in trades if t.get("tradeType", "").startswith("Purchase")]

    for purchase in purchases:
        ticker     = purchase.get("ticker", "")
        trade_date = purchase.get("tradeDate", "")
        amount_min = purchase.get("amount", {}).get("min", 0)
        amount_max = purchase.get("amount", {}).get("max", 0)
        weight     = (amount_min + amount_max) / 2  # midpoint

        if not ticker or not trade_date or weight <= 0:
            continue

        prices = price_histories.get(ticker, {})
        entry_price = _price_on_date(prices, trade_date)
        if not entry_price:
            continue

        # Look for a matching sale after this purchase
        exit_price = None
        matching_sales = [
            t for t in trades
            if t.get("ticker") == ticker
            and t.get("tradeType", "").startswith("Sale")
            and t.get("tradeDate", "") > trade_date
        ]
        if matching_sales:
            # Use the first sale after the purchase
            sale = min(matching_sales, key=lambda t: t.get("tradeDate", ""))
            exit_price = _price_on_date(prices, sale["tradeDate"])

        if exit_price is None:
            # Still holding — use today's price
            today_str = today.strftime("%Y-%m-%d")
            exit_price = _price_on_date(prices, today_str)

        if exit_price is None or entry_price <= 0:
            continue

        position_return = ((exit_price - entry_price) / entry_price) * 100.0
        weighted_return += position_return * weight
        total_weight    += weight

    if total_weight <= 0:
        return None

    return weighted_return / total_weight


def _price_on_date(prices: dict[str, float], target_date: str) -> Optional[float]:
    """Get closing price for target_date or nearest prior trading day."""
    if not prices:
        return None
    if target_date in prices:
        return prices[target_date]
    # Find nearest prior date
    available = sorted([d for d in prices.keys() if d <= target_date])
    if available:
        return prices[available[-1]]
    return None


def _get_sp_window_return(sp_returns: dict[str, float], years: int) -> Optional[float]:
    """Calculate compound S&P 500 return over N years."""
    today = date.today()
    relevant_years = []
    for y in range(today.year - years, today.year + 1):
        val = sp_returns.get(str(y))
        if val is not None:
            relevant_years.append(val)
    if not relevant_years:
        return None
    # Compound: product of (1 + r/100) - 1
    compound = 1.0
    for r in relevant_years:
        compound *= (1 + r / 100)
    return (compound - 1) * 100


def _assign_badge(ret_1y: Optional[float], excess_1y: Optional[float]) -> str:
    if ret_1y is None:
        return "Insufficient Data"
    if excess_1y is not None and excess_1y >= BADGE_HIGH_OUTPERFORM:
        return "High Outperformance"
    if excess_1y is not None and excess_1y >= BADGE_STRONG_GAINS:
        return "Strong Estimated Gains"
    if ret_1y >= BADGE_WATCHLIST:
        return "Watchlist"
    if excess_1y is not None and abs(excess_1y) <= BADGE_MARKET_TRACKING:
        return "Market-Tracking"
    if ret_1y <= BADGE_UNDERPERFORMING:
        return "Underperforming"
    return "Market-Tracking"


def _empty_snapshot(member: dict, badge: str, caveats: list) -> dict:
    return {
        "memberId":          member["id"],
        "memberName":        member["name"],
        "memberSlug":        member["slug"],
        "estimatedReturn1y": None,
        "estimatedReturn3y": None,
        "estimatedReturn5y": None,
        "spReturn1y":        None,
        "spReturn3y":        None,
        "spReturn5y":        None,
        "excessReturn1y":    None,
        "excessReturn3y":    None,
        "excessReturn5y":    None,
        "confidence":        "low",
        "badge":             badge,
        "tradeCount":        0,
        "methodology":       "Insufficient data for estimation",
        "caveats":           caveats,
    }


def _round(v: Optional[float], decimals: int = 2) -> Optional[float]:
    if v is None:
        return None
    return round(v, decimals)


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()
