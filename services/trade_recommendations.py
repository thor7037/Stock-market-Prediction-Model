"""Trade recommendation helpers for index options and intraday stock ideas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

from services.global_markets import INVESTOR_MARKETS
from services.yf_helpers import download_daily, flatten_columns

_STOCK_UNIVERSE = (
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT"},
    {"symbol": "TCS.NS", "name": "TCS", "sector": "IT"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Industrials"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "sector": "Banking"},
    {"symbol": "ITC.NS", "name": "ITC", "sector": "FMCG"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecom"},
)

_SECTOR_WEIGHT = {
    "Banking": 1.15,
    "IT": 1.05,
    "Energy": 1.0,
    "Industrials": 0.95,
    "FMCG": 0.9,
    "Telecom": 0.9,
}


@dataclass(frozen=True)
class StockIdea:
    symbol: str
    name: str
    sector: str
    score: float
    signal: str
    reason: str
    entry_bias: str


def _normalize_weighted_scores(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(float(row["impact_weight"]) for row in rows) or 1.0
    for row in rows:
        row["normalized_weight_pct"] = round((float(row["impact_weight"]) / total) * 100, 2)
    return rows


def build_country_impact_analysis() -> list[dict[str, Any]]:
    """Return country impact share normalized to 100%."""
    rows = [
        {
            "key": market.key,
            "country": market.country,
            "market": market.market_name,
            "impact_weight": market.impact_pct,
            "session_ist": f"{market.open_ist}–{market.close_ist}",
            "notes": market.notes,
        }
        for market in INVESTOR_MARKETS
    ]
    return _normalize_weighted_scores(rows)


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _score_frame(df: pd.DataFrame) -> dict[str, float]:
    close = df["Close"].squeeze()

    rsi = float(RSIIndicator(close=close).rsi().iloc[-1])
    ema20 = float(EMAIndicator(close=close, window=20).ema_indicator().iloc[-1])
    macd = float(MACD(close=close).macd().iloc[-1])

    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
    )
    atr_pct = float((atr.average_true_range() / df["Close"]).iloc[-1])

    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else price
    momentum = ((price - prev) / prev) * 100 if prev else 0.0
    ema_gap = ((price - ema20) / price) * 100 if price else 0.0
    range_pct = float(((df["High"].iloc[-1] - df["Low"].iloc[-1]) / price) * 100) if price else 0.0

    return {
        "rsi": rsi,
        "macd": macd,
        "atr_pct": atr_pct,
        "momentum": momentum,
        "ema_gap": ema_gap,
        "range_pct": range_pct,
        "price": price,
    }


def _direction_from_scores(scores: dict[str, float]) -> tuple[str, str, float]:
    momentum = scores["momentum"]
    rsi = scores["rsi"]
    ema_gap = scores["ema_gap"]
    macd = scores["macd"]

    bullish_points = 0.0
    bearish_points = 0.0

    bullish_points += max(momentum, 0) * 1.4
    bearish_points += max(-momentum, 0) * 1.4

    if rsi >= 55:
        bullish_points += (rsi - 55) * 0.03
    elif rsi <= 45:
        bearish_points += (45 - rsi) * 0.03

    bullish_points += max(ema_gap, 0) * 1.8
    bearish_points += max(-ema_gap, 0) * 1.8

    if macd > 0:
        bullish_points += min(macd * 8, 2.0)
    else:
        bearish_points += min(abs(macd) * 8, 2.0)

    bullish_points = round(bullish_points, 3)
    bearish_points = round(bearish_points, 3)

    if bullish_points > bearish_points + 0.35:
        return "Bullish", "Trend is improving and momentum is positive", bullish_points - bearish_points
    if bearish_points > bullish_points + 0.35:
        return "Bearish", "Trend is weakening and downside pressure is visible", bearish_points - bullish_points
    return "Sideways", "No strong directional edge", abs(bullish_points - bearish_points)


def build_stock_ideas(limit: int = 5) -> list[dict[str, Any]]:
    """Generate a small intraday-style list of liquid stocks with directional bias."""
    ideas: list[StockIdea] = []

    for stock in _STOCK_UNIVERSE:
        df = download_daily(stock["symbol"], periods=("5d", "1mo", "3mo"))
        df = flatten_columns(df)
        if df.empty or len(df) < 20:
            continue
        if not all(c in df.columns for c in ("Open", "High", "Low", "Close", "Volume")):
            continue

        scores = _score_frame(df)
        signal, reason, strength = _direction_from_scores(scores)
        sector = stock["sector"]
        sector_multiplier = _SECTOR_WEIGHT.get(sector, 1.0)

        composite = (
            (scores["momentum"] * 0.35)
            + ((scores["rsi"] - 50) * 0.03)
            + (scores["ema_gap"] * 1.2)
            + (scores["macd"] * 0.8)
        ) * sector_multiplier

        if signal == "Bullish":
            entry_bias = "Buy on dips / momentum continuation"
        elif signal == "Bearish":
            entry_bias = "Sell on rallies / weak rebound fade"
        else:
            entry_bias = "Wait for breakout confirmation"

        ideas.append(
            StockIdea(
                symbol=stock["symbol"],
                name=stock["name"],
                sector=sector,
                score=round(composite, 3),
                signal=signal,
                reason=reason,
                entry_bias=entry_bias,
            )
        )

    ideas = sorted(ideas, key=lambda x: x.score, reverse=True)
    return [
        {
            "symbol": idea.symbol,
            "name": idea.name,
            "sector": idea.sector,
            "score": idea.score,
            "signal": idea.signal,
            "reason": idea.reason,
            "entry_bias": idea.entry_bias,
        }
        for idea in ideas[:limit]
    ]


def build_index_trade_summary(global_signal: dict, fii_dii: dict) -> dict[str, Any]:
    """Summarize index options bias using global markets and FII/DII."""
    composite = _safe_float(global_signal.get("composite_score", 0))
    confidence = _safe_float(global_signal.get("confidence", 0))
    fii_score = _safe_float(fii_dii.get("score", 0))

    if composite > 0.25:
        bias = "Bullish"
    elif composite < -0.25:
        bias = "Bearish"
    else:
        bias = "Sideways"

    if bias == "Bullish":
        trade_type = "Call spread / Buy CE on confirmation"
    elif bias == "Bearish":
        trade_type = "Put spread / Buy PE on confirmation"
    else:
        trade_type = "Iron condor / range selling"

    if _safe_float(fii_dii.get("net", 0)) > 0:
        fii_view = "Net institutional support"
    elif _safe_float(fii_dii.get("net", 0)) < 0:
        fii_view = "Net institutional selling"
    else:
        fii_view = "Balanced flow"

    return {
        "bias": bias,
        "confidence": round(confidence, 1),
        "trade_type": trade_type,
        "fii_view": fii_view,
        "fii_dii_score": round(fii_score, 2),
        "options_hint": global_signal.get("options_hint", ""),
        "expected_move_pct": global_signal.get("expected_move_pct", 0),
    }
