"""Shared feature engineering aligned with index classifier training."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

from services.yf_helpers import DEFAULT_PERIODS_LONG, download_daily, flatten_columns

_MIN_TREND_THRESHOLD = 0.0025
_SIDEWAYS_MULTIPLIER = 0.6


def _squeeze(series):
    return series.squeeze() if hasattr(series, "squeeze") else series


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    return out


def _vix_close_column(df: pd.DataFrame) -> str | None:
    for name in ("VIX_Close", "VIX Close", "VIX_CLOSE"):
        if name in df.columns:
            return name
    matches = [
        c
        for c in df.columns
        if "vix" in str(c).lower() and "close" in str(c).lower()
    ]
    return matches[0] if matches else None


def _prefix_vix_columns(vix: pd.DataFrame) -> pd.DataFrame:
    vix = _flatten_columns(vix)
    if vix.empty:
        return pd.DataFrame()

    needed = ["Open", "High", "Low", "Close", "Volume"]
    if not all(c in vix.columns for c in needed):
        return pd.DataFrame()

    vix = vix[needed].copy()
    vix.columns = [f"VIX_{c}" for c in vix.columns]
    return vix


def _add_price_action_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["RETURN"] = out["Close"].pct_change()
    out["RETURN_3"] = out["Close"].pct_change(3)
    out["RETURN_5"] = out["Close"].pct_change(5)
    out["RETURN_10"] = out["Close"].pct_change(10)

    close = _squeeze(out["Close"])
    high = _squeeze(out["High"])
    low = _squeeze(out["Low"])
    open_ = _squeeze(out["Open"])
    volume = _squeeze(out["Volume"])

    out["RSI"] = RSIIndicator(close=close).rsi()
    out["EMA20"] = EMAIndicator(close=close, window=20).ema_indicator()
    out["EMA50"] = EMAIndicator(close=close, window=50).ema_indicator()
    out["MACD"] = MACD(close=close).macd()
    out["MACD_SIGNAL"] = MACD(close=close).macd_signal()

    atr = AverageTrueRange(high=high, low=low, close=close)
    out["ATR"] = atr.average_true_range()
    out["ATR_PCT"] = out["ATR"] / out["Close"]
    out["VOL_THRESHOLD"] = out["ATR_PCT"]

    out["RANGE"] = out["High"] - out["Low"]
    out["BODY"] = out["Close"] - out["Open"]
    out["UPPER_WICK"] = out["High"] - out[["Open", "Close"]].max(axis=1)
    out["LOWER_WICK"] = out[["Open", "Close"]].min(axis=1) - out["Low"]

    out["EMA_DISTANCE"] = (out["Close"] - out["EMA20"]) / out["Close"]
    out["EMA_SLOPE"] = out["EMA20"].pct_change()
    out["VOL_MA20"] = pd.Series(volume).rolling(20).mean()
    out["VOLUME_RATIO"] = out["Volume"] / out["VOL_MA20"]

    vix_col = _vix_close_column(out)
    if vix_col is not None:
        out["VIX_CHANGE"] = out[vix_col].pct_change()
        out["VIX_RANGE"] = (out.get("VIX_High", out[vix_col]) - out.get("VIX_Low", out[vix_col])) / out[vix_col]
    else:
        out["VIX_CHANGE"] = 0.0
        out["VIX_RANGE"] = 0.0

    out["MOMENTUM_3"] = out["Close"].pct_change(3)
    out["MOMENTUM_5"] = out["Close"].pct_change(5)

    return out


def _add_target_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["NEXT_DAY_RETURN"] = (out["Close"].shift(-1) / out["Close"]) - 1
    out["ABS_NEXT_DAY_RETURN"] = out["NEXT_DAY_RETURN"].abs()

    threshold = (out["VOL_THRESHOLD"] * _SIDEWAYS_MULTIPLIER).clip(lower=_MIN_TREND_THRESHOLD)

    out["Target"] = 1
    out.loc[out["NEXT_DAY_RETURN"] > threshold, "Target"] = 2
    out.loc[out["NEXT_DAY_RETURN"] < -threshold, "Target"] = 0

    out["Direction"] = out["Target"].map({0: "Bearish", 1: "Sideways", 2: "Bullish"})

    return out


def _finalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.ffill().dropna().reset_index(drop=True)
    out = out.replace([pd.NA, float("inf"), float("-inf")], pd.NA).dropna()
    return out.reset_index(drop=True)


@lru_cache(maxsize=4)
def _load_vix_frame(period: str = "6mo") -> pd.DataFrame:
    periods = (period,) + DEFAULT_PERIODS_LONG
    vix = download_daily("^INDIAVIX", periods=periods)
    vix = flatten_columns(vix)
    if vix.empty:
        return pd.DataFrame()
    return _prefix_vix_columns(vix)


@lru_cache(maxsize=8)
def build_index_vix_frame(symbol: str = "^NSEI", period: str = "6mo") -> pd.DataFrame:
    periods = (period,) + DEFAULT_PERIODS_LONG
    index = download_daily(symbol, periods=periods)
    index = flatten_columns(index)
    if index.empty:
        return pd.DataFrame()

    needed = ["Open", "High", "Low", "Close", "Volume"]
    if not all(c in index.columns for c in needed):
        return pd.DataFrame()

    index = index[needed].copy()
    index.columns = ["Open", "High", "Low", "Close", "Volume"]

    vix = _load_vix_frame(period)
    if vix.empty:
        return _finalize_frame(index)

    df = pd.concat([index, vix], axis=1)
    df = df.loc[:, ~df.columns.duplicated()]
    return _finalize_frame(df)


def build_nifty_vix_frame(period: str = "6mo") -> pd.DataFrame:
    return build_index_vix_frame("^NSEI", period=period)


def enrich_index_features(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = _add_price_action_features(df)
    return _finalize_frame(out)


def build_training_frame(symbol: str = "^NSEI", period: str = "10y") -> pd.DataFrame:
    base = build_index_vix_frame(symbol, period=period)
    if base.empty:
        return pd.DataFrame()
    framed = _add_price_action_features(base)
    framed = _add_target_columns(framed)
    return _finalize_frame(framed)


def latest_model_features(symbol: str = "^NSEI") -> pd.DataFrame | None:
    df = enrich_index_features(build_index_vix_frame(symbol))
    if df.empty:
        return None
    return df.iloc[[-1]].copy()


def clear_feature_cache() -> None:
    build_index_vix_frame.cache_clear()
    _load_vix_frame.cache_clear()
