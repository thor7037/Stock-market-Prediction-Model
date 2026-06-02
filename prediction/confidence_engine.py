"""Confidence scoring for predictions."""


def compute_confidence(signals: dict) -> float:
    values = []
    for value in signals.values():
        if isinstance(value, (int, float)):
            values.append(abs(float(value)))
        elif isinstance(value, dict) and "confidence" in value:
            values.append(float(value["confidence"]) / 100)

    if not values:
        return 50.0

    confidence = 40 + min(sum(values) / len(values), 1.0) * 55
    return round(confidence, 2)
