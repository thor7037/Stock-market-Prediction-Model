"""Yahoo Finance market data for global lead markets and Indian indices."""

from __future__ import annotations

import pandas as pd

from services.yf_helpers import DEFAULT_PERIODS_SHORT, download_daily, flatten_columns

from services.global_markets import INDIA_INDICES, INVESTOR_MARKETS


def _scalar(value) -> float:
    if hasattr(value, "squeeze"):
        value = value.squeeze()
    if isinstance(value, pd.Series):
        value = value.iloc[-1] if len(value) else 0
    return float(value)


_EMPTY = {
    "open": 0.0,
    "high": 0.0,
    "low": 0.0,
    "current": 0.0,
    "points": 0.0,
    "percentage": 0.0,
    "range_pct": 0.0,
    "close_in_range": 0.5,
}


def _row_to_snapshot(df: pd.DataFrame) -> dict | None:
    if df is None or df.empty or len(df) < 2:
        return None
    df = flatten_columns(df)
    if "Close" not in df.columns:
        return None

    row = df.iloc[-1]
    prev_close = _scalar(df["Close"].iloc[-2])

    open_ = _scalar(row["Open"]) if "Open" in df.columns else prev_close
    high = _scalar(row["High"]) if "High" in df.columns else _scalar(row["Close"])
    low = _scalar(row["Low"]) if "Low" in df.columns else _scalar(row["Close"])
    close = _scalar(row["Close"])

    points = round(close - prev_close, 2)
    percentage = round((points / prev_close) * 100, 2) if prev_close else 0.0
    range_pct = round(((high - low) / close) * 100, 2) if close else 0.0
    close_in_range = round((close - low) / (high - low), 3) if high > low else 0.5

    return {
        "open": round(open_, 2),
        "high": round(high, 2),
        "low": round(low, 2),
        "current": round(close, 2),
        "points": points,
        "percentage": percentage,
        "range_pct": range_pct,
        "close_in_range": close_in_range,
    }


def safe_fetch_ohlc(symbol: str, period: str | None = None) -> dict | None:
    """
    Fetch latest daily OHLC snapshot. Uses period fallbacks + Ticker.history
    (see services.yf_helpers.download_daily).
    """
    periods = (period,) if period else DEFAULT_PERIODS_SHORT
    df = download_daily(symbol, periods=periods)
    return _row_to_snapshot(df)


def snapshot_from_manual(
    high: float,
    low: float,
    close: float,
    percentage: float | None = None,
) -> dict:
    """Build a market snapshot from user-supplied H/L/C or % change."""
    if close <= 0:
        return dict(_EMPTY)

    range_pct = round(((high - low) / close) * 100, 2)
    close_in_range = round((close - low) / (high - low), 3) if high > low else 0.5

    if percentage is None and high != low:
        open_est = low + (high - low) * 0.3
        percentage = round(((close - open_est) / open_est) * 100, 2)
    else:
        percentage = float(percentage or 0)

    return {
        "open": round(close * (1 - percentage / 100), 2),
        "high": round(high, 2),
        "low": round(low, 2),
        "current": round(close, 2),
        "points": 0.0,
        "percentage": round(percentage, 2),
        "range_pct": range_pct,
        "close_in_range": close_in_range,
    }


def _first_successful_symbol(symbols: tuple[str, ...]) -> dict | None:
    for sym in symbols:
        data = safe_fetch_ohlc(sym)
        if data and data.get("current", 0):
            return data
    return None


def fetch_investor_markets() -> dict[str, dict]:
    result = {}
    for market in INVESTOR_MARKETS:
        syms = (market.symbol,) + market.symbol_alternates
        data = _first_successful_symbol(syms)
        result[market.key] = data if data else dict(_EMPTY)
    return result


def fetch_india_indices() -> dict[str, dict]:
    result = {}
    for key, meta in INDIA_INDICES.items():
        syms = (meta["symbol"],) + tuple(meta.get("symbol_alternates", ()))
        data = _first_successful_symbol(syms)
        result[key] = data if data else dict(_EMPTY)
    return result


def fetch_global_market_data() -> dict:
    """Backward-compatible bundle for existing callers."""
    investor = fetch_investor_markets()
    india = fetch_india_indices()

    return {
        **investor,
        **india,
        "nasdaq": safe_fetch_ohlc("^IXIC") or dict(_EMPTY),
        "dow": safe_fetch_ohlc("^DJI") or dict(_EMPTY),
        "sp500": investor.get("united_states", dict(_EMPTY)),
        "nikkei": investor.get("japan", dict(_EMPTY)),
        "hangseng": safe_fetch_ohlc("^HSI") or dict(_EMPTY),
        "crudeOil": safe_fetch_ohlc("BZ=F") or dict(_EMPTY),
        "dxy": safe_fetch_ohlc("DX-Y.NYB") or dict(_EMPTY),
        "vix": safe_fetch_ohlc("^INDIAVIX") or dict(_EMPTY),
        "nifty": india.get("nifty", dict(_EMPTY)),
        "banknifty": india.get("banknifty", dict(_EMPTY)),
        "finnifty": india.get("finnifty", dict(_EMPTY)),
        "sensex": india.get("sensex", dict(_EMPTY)),
    }
