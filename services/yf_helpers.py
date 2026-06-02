"""Resilient Yahoo Finance access (retries, period fallbacks, failed-symbol cache)."""

from __future__ import annotations

import logging
import time

import pandas as pd
import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

DEFAULT_PERIODS_SHORT = ("5d", "1mo", "6mo")
DEFAULT_PERIODS_LONG = ("3mo", "6mo", "1y", "2y")
_RETRIES = 2
_RETRY_DELAY_SEC = 0.6

_FAILED_SYMBOLS: set[str] = set()


def clear_failed_symbols() -> None:
    """Call on Streamlit cache clear so refresh can retry Yahoo."""
    _FAILED_SYMBOLS.clear()


def flatten_columns(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    return out


def _mark_failed(symbol: str) -> None:
    _FAILED_SYMBOLS.add(symbol)


def download_daily(
    symbol: str,
    periods: tuple[str, ...] = DEFAULT_PERIODS_SHORT,
) -> pd.DataFrame:
    if symbol in _FAILED_SYMBOLS:
        return pd.DataFrame()

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
            except Exception:
                pass

        try:
            df = yf.Ticker(symbol).history(period="6mo", interval="1d", auto_adjust=True)
            if df is not None and not df.empty and len(df) >= 2:
                return flatten_columns(df.rename(columns=str.title))
        except Exception:
            pass

        if attempt + 1 < _RETRIES:
            time.sleep(_RETRY_DELAY_SEC)

    _mark_failed(symbol)
    return pd.DataFrame()


def download_batch_daily(
    symbols: tuple[str, ...],
    period: str = "5d",
) -> dict[str, pd.DataFrame]:
    """One round-trip for multiple tickers; skips symbols in failed cache."""
    out: dict[str, pd.DataFrame] = {}
    pending = [s for s in symbols if s and s not in _FAILED_SYMBOLS]
    if not pending:
        return out

    try:
        raw = yf.download(
            " ".join(pending),
            period=period,
            interval="1d",
            progress=False,
            threads=False,
            group_by="ticker",
        )
    except Exception:
        return out

    if raw is None or raw.empty:
        return out

    if isinstance(raw.columns, pd.MultiIndex):
        tickers = raw.columns.get_level_values(0).unique()
        for ticker in tickers:
            try:
                part = raw[ticker].dropna()
                if len(part) >= 2:
                    out[str(ticker)] = flatten_columns(part)
            except (KeyError, TypeError):
                continue
    else:
        sym = pending[0] if len(pending) == 1 else None
        if sym:
            df = flatten_columns(raw)
            if len(df) >= 2:
                out[sym] = df

    return out
