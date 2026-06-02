"""Adaptive weighting for signal components."""


def get_weights(regime: str) -> dict:
    regime = (regime or "neutral").lower()

    if regime == "trending":
        return {"technical": 0.45, "global": 0.35, "sentiment": 0.2}
    if regime == "volatile":
        return {"technical": 0.3, "global": 0.45, "sentiment": 0.25}
    if regime == "ranging":
        return {"technical": 0.4, "global": 0.25, "sentiment": 0.35}

    return {"technical": 0.4, "global": 0.4, "sentiment": 0.2}
