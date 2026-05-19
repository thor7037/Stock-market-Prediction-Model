"""India market predictions: ML model + global pre-India composite."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from ml.feature_utils import latest_model_features
from services.global_markets import INDIA_INDICES, INDEX_MOVE_BETA
from services.pre_india_signal import compute_pre_india_signal

MODEL_PATH = Path("ml/nifty_model.pkl")
CLASSES = ["Bearish", "Sideways", "Bullish"]


@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def _ml_prediction() -> dict | None:
    model = _load_model()
    if model is None:
        return None

    try:
        row = latest_model_features()
    except Exception as exc:
        print(f"ML feature error: {exc}")
        return None

    if row is None or row.empty:
        return None

    feature_names = list(model.get_booster().feature_names)
    drop_cols = [c for c in ("Target",) if c in row.columns]
    X = row.drop(columns=drop_cols, errors="ignore")
    X = X.reindex(columns=feature_names, fill_value=0)

    pred = int(model.predict(X)[0])
    probs = model.predict_proba(X)[0]

    move_pct = round((float(probs[2]) - float(probs[0])) * 100, 2)

    return {
        "sentiment": CLASSES[pred],
        "confidence": round(float(max(probs)) * 100, 2),
        "expected_move_pct": abs(move_pct),
        "probabilities": {
            "Bearish": round(float(probs[0]) * 100, 2),
            "Sideways": round(float(probs[1]) * 100, 2),
            "Bullish": round(float(probs[2]) * 100, 2),
        },
        "source": "xgboost",
    }


def _blend_predictions(ml: dict | None, global_sig: dict) -> dict:
    if ml is None:
        return {
            **global_sig,
            "expected_move_pct": global_sig["expected_move_pct"],
            "probabilities": {
                "Bearish": 33.0,
                "Sideways": 34.0,
                "Bullish": 33.0,
            },
            "source": "global_composite",
        }

    g_score = global_sig["composite_score"]
    agree = (
        (g_score > 0.15 and ml["sentiment"] == "Bullish")
        or (g_score < -0.15 and ml["sentiment"] == "Bearish")
        or (abs(g_score) <= 0.15 and ml["sentiment"] == "Sideways")
    )

    confidence = ml["confidence"]
    if agree:
        confidence = min(95.0, confidence + 8)

    expected_move = round(
        (ml["expected_move_pct"] + global_sig["expected_move_pct"]) / 2,
        2,
    )

    return {
        "sentiment": ml["sentiment"],
        "confidence": round(confidence, 2),
        "expected_move_pct": expected_move,
        "probabilities": ml["probabilities"],
        "options_hint": global_sig["options_hint"],
        "composite_score": global_sig["composite_score"],
        "source": "blended",
    }


def predict_india(
    investor_snapshots: dict[str, dict],
    india_indices: dict[str, dict],
) -> dict:
    global_sig = compute_pre_india_signal(investor_snapshots)
    ml = _ml_prediction()
    core = _blend_predictions(ml, global_sig)

    indices_out = []
    nifty_price = float(india_indices.get("nifty", {}).get("current", 0) or 0)

    for key, meta in INDIA_INDICES.items():
        price = float(india_indices.get(key, {}).get("current", 0) or 0)
        beta = INDEX_MOVE_BETA.get(key, 1.0)
        move_pct = round(core["expected_move_pct"] * beta, 2)
        if core["sentiment"] == "Bearish":
            move_pct = -move_pct

        indices_out.append(
            {
                "index": meta["name"],
                "key": key,
                "sentiment": core["sentiment"],
                "confidence": core["confidence"],
                "expectedMove": move_pct,
                "expectedPoints": round((move_pct / 100) * price, 2) if price else 0,
                "currentPrice": price,
                "probabilities": core["probabilities"],
                "options_hint": core.get("options_hint", global_sig["options_hint"]),
            }
        )

    return {
        "core": core,
        "global_signal": global_sig,
        "indices": indices_out,
        "nifty_price": nifty_price,
    }


def predict_all_indices(market_data: dict, technical_data: dict | None = None) -> list[dict]:
    """Backward-compatible API for app.py."""
    investor_keys = {
        "japan",
        "singapore",
        "uae",
        "united_states",
        "canada",
        "united_kingdom",
        "norway",
    }
    investor = {k: market_data[k] for k in investor_keys if k in market_data}
    india = {
        k: market_data[k]
        for k in ("nifty", "banknifty", "finnifty", "sensex")
        if k in market_data
    }
    result = predict_india(investor, india)
    return result["indices"]
