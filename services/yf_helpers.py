"""Resilient Yahoo Finance access (retries, period fallbacks, Ticker.history)."""

from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

DEFAULT_PERIODS_SHORT = ("5d", "1mo", "3mo", "6mo", "1y", "max")
DEFAULT_PERIODS_LONG = ("3mo", "6mo", "1y", "2y", "max")
_RETRIES = 2
_RETRY_DELAY_SEC = 0.6


def flatten_columns(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    return out


def download_daily(
    symbol: str,
    periods: tuple[str, ...] = DEFAULT_PERIODS_SHORT,
) -> pd.DataFrame:
    for attempt in range(_RETRIES):
        for period in periods:
            try:
                df = yf.download(
                    symbol,
                    period=period,
                    interval="1d",
                    progress=False,
                    threads=False,
                )
                df = flatten_columns(df)
                if not df.empty and len(df) >= 2:
                    return df
            except Exception as exc:
                print(f"yfinance download [{symbol}] {period}: {exc}")

        try:
            df = yf.Ticker(symbol).history(period="2y", interval="1d", auto_adjust=True)
            if df is not None and not df.empty and len(df) >= 2:
                return flatten_columns(df.rename(columns=str.title))
        except Exception as exc:
            print(f"yfinance history [{symbol}]: {exc}")

        if attempt + 1 < _RETRIES:
            time.sleep(_RETRY_DELAY_SEC)

    return pd.DataFrame()
