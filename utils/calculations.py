"""Common financial calculations."""

import numpy as np
import pandas as pd


def pct_change(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.pct_change(periods=periods) * 100


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    excess = returns - risk_free
    if excess.std() == 0:
        return 0.0
    return float(np.sqrt(252) * excess.mean() / excess.std())
