"""Supertrend indicator."""

import pandas as pd

from indicators.atr import atr


def supertrend(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 10,
    multiplier: float = 3.0,
):
    atr_vals = atr(high, low, close, period)
    hl2 = (high + low) / 2
    upper = hl2 + multiplier * atr_vals
    lower = hl2 - multiplier * atr_vals
    return upper, lower
