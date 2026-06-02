"""Run inference with trained models."""

from pathlib import Path

import joblib

MODEL_PATH = Path("ml/nifty_model.pkl")


def predict(features):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)
    feature_names = list(model.get_booster().feature_names)
    X = features.reindex(columns=feature_names, fill_value=0)
    return model.predict(X)
