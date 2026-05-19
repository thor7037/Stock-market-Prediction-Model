"""
Weighted composite from global market snapshots → India direction hint.
"""

from __future__ import annotations

from services.global_markets import INVESTOR_MARKETS, MARKET_BY_KEY


def _direction_score(snapshot: dict) -> float:
    """Map day stats to [-1, 1] bullish/bearish score."""
    pct = float(snapshot.get("percentage", 0) or 0)
    close_in_range = snapshot.get("close_in_range")
    range_pct = float(snapshot.get("range_pct", 0) or 0)

    score = pct / 1.5  # ~1.5% day ≈ full tilt

    if close_in_range is not None:
        score += (float(close_in_range) - 0.5) * 0.8

    if range_pct > 2.5:
        score *= 1.15  # wide range day amplifies signal

    return max(-1.0, min(1.0, score))


def compute_pre_india_signal(snapshots: dict[str, dict]) -> dict:
    """
    snapshots: {market_key: {percentage, range_pct, close_in_range, ...}}
    """
    total_weight = 0.0
    weighted = 0.0
    breakdown = []

    for market in INVESTOR_MARKETS:
        snap = snapshots.get(market.key)
        if not snap:
            continue

        w = market.impact_pct
        s = _direction_score(snap)
        contrib = w * s
        weighted += contrib
        total_weight += w

        breakdown.append(
            {
                "key": market.key,
                "country": market.country,
                "impact_pct": market.impact_pct,
                "score": round(s, 3),
                "contribution": round(contrib, 2),
                "percentage": snap.get("percentage", 0),
                "range_pct": snap.get("range_pct", 0),
            }
        )

    if total_weight == 0:
        composite = 0.0
    else:
        composite = weighted / total_weight

    if composite > 0.25:
        sentiment = "Bullish"
    elif composite < -0.25:
        sentiment = "Bearish"
    else:
        sentiment = "Sideways"

    expected_move_pct = round(abs(composite) * 1.2, 2)

    if composite > 0.35:
        options_hint = "Favor CE / call spreads (bullish bias)"
    elif composite < -0.35:
        options_hint = "Favor PE / put spreads (bearish bias)"
    elif expected_move_pct < 0.35:
        options_hint = "Low edge — avoid aggressive directional options"
    else:
        options_hint = "Mixed — consider iron condor / reduced size"

    return {
        "composite_score": round(composite, 3),
        "sentiment": sentiment,
        "expected_move_pct": expected_move_pct,
        "confidence": round(min(95, abs(composite) * 100 + 40), 1),
        "options_hint": options_hint,
        "breakdown": breakdown,
    }
