"""FII/DII flow signal — stable per calendar day until live NSE feed is wired."""

from __future__ import annotations

import hashlib
import random
from datetime import date
from functools import lru_cache

# Replace with real NSE / NSDL fetch when available.
_DEMO_NOTE = "Demo values fixed for the trading day (not live NSE data)."


@lru_cache(maxsize=8)
def fetch_fii_dii_data(trading_day: str) -> dict:
    rng = random.Random(
        int(hashlib.sha256(trading_day.encode()).hexdigest()[:12], 16)
    )
    fii = rng.randint(-2800, 2800)
    dii = rng.randint(-1800, 1800)
    return {
        "fii": fii,
        "dii": dii,
        "net": fii + dii,
        "trading_day": trading_day,
        "source": "demo_daily",
    }


def clear_fii_dii_cache() -> None:
    fetch_fii_dii_data.cache_clear()


def get_fii_dii_signal(trading_day: str | None = None) -> dict:
    day = trading_day or date.today().isoformat()
    data = fetch_fii_dii_data(day)

    fii = data["fii"]
    dii = data["dii"]

    score = fii / 2000 + dii / 4000
    score = max(min(score, 1.0), -1.0)

    if score > 0.2:
        sentiment = "Bullish"
    elif score < -0.2:
        sentiment = "Bearish"
    else:
        sentiment = "Sideways"

    return {
        "score": round(score, 2),
        "sentiment": sentiment,
        "fii": fii,
        "dii": dii,
        "net": data["net"],
        "trading_day": day,
        "source": data["source"],
        "note": _DEMO_NOTE,
    }
