"""Shared feature engineering aligned with nifty_model.pkl training."""

from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

from services.yf_helpers import DEFAULT_PERIODS_LONG, download_daily, flatten_columns


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
    """Resolve VIX close column name across yfinance / dataset variants."""
    for name in ("VIX_Close", "VIX Close", "VIX_CLOSE"):
        if name in df.columns:
            return name
    matches = [c for c in df.columns if "vix" in str(c).lower() and "close" in str(c).lower()]
    return matches[0] if matches else None


def _prefix_vix_columns(vix: pd.DataFrame) -> pd.DataFrame:
    """Match dataset_builder: VIX_Open, VIX_Close, ..."""
    vix = _flatten_columns(vix)
    if vix.empty:
        return pd.DataFrame()

    needed = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in needed if c not in vix.columns]
    if missing:
        return pd.DataFrame()

    vix = vix[needed].copy()
    vix.columns = [f"VIX_{c}" for c in vix.columns]
    return vix


def build_nifty_vix_frame(period: str = "6mo") -> pd.DataFrame:
    periods = (period,) + DEFAULT_PERIODS_LONG
    nifty = download_daily("^NSEI", periods=periods)
    vix = download_daily("^INDIAVIX", periods=periods)

    nifty = flatten_columns(nifty)
    if nifty.empty:
        return pd.DataFrame()

    needed = ["Open", "High", "Low", "Close", "Volume"]
    if not all(c in nifty.columns for c in needed):
        return pd.DataFrame()

    nifty = nifty[needed].copy()
    nifty.columns = ["Open", "High", "Low", "Close", "Volume"]

    vix = flatten_columns(vix)
    if vix.empty:
        return nifty.dropna()

    vix = _prefix_vix_columns(vix)
    if vix.empty:
        return nifty.dropna()

    df = pd.concat([nifty, vix], axis=1)
    df = df.loc[:, ~df.columns.duplicated()]
    return df.ffill().dropna()


def enrich_nifty_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    close = _squeeze(out["Close"])

    out["RETURN"] = out["Close"].pct_change()
    out["RSI"] = RSIIndicator(close=close).rsi()
    out["EMA20"] = EMAIndicator(close=close, window=20).ema_indicator()
    out["MACD"] = MACD(close=close).macd()

    atr = AverageTrueRange(
        high=out["High"],
        low=out["Low"],
        close=out["Close"],
    )
    out["ATR"] = atr.average_true_range()
    out["RANGE"] = out["High"] - out["Low"]

    vix_col = _vix_close_column(out)
    if vix_col is not None:
        out["VIX_CHANGE"] = out[vix_col].pct_change()
    else:
        out["VIX_CHANGE"] = 0.0

    out["MOMENTUM_3"] = out["Close"].pct_change(3)
    out["MOMENTUM_5"] = out["Close"].pct_change(5)

    return out.dropna()


def latest_model_features() -> pd.DataFrame | None:
    """One-row feature matrix for the trained classifier."""
    df = enrich_nifty_features(build_nifty_vix_frame())
    if df.empty:
        return None
    return df.iloc[[-1]].copy()
