"""India market predictions: ML + global + FII/DII + strategy + risk + entry."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import joblib

from ml.feature_utils import latest_model_features
from services.global_markets import INDIA_INDICES, INDEX_MOVE_BETA
from services.pre_india_signal import compute_pre_india_signal
from services.trade_recommendations import (
    build_country_impact_analysis,
    build_index_trade_summary,
    build_stock_ideas,
)
from services.strike_selector import get_option_strategy
from services.risk_manager import get_risk_plan
from services.entry_timing import get_entry_plan
from services.fii_dii import get_fii_dii_signal


CLASSES = ["Bearish", "Sideways", "Bullish"]

MODEL_PATHS = {
    "nifty": Path("ml/nifty_model.pkl"),
    "banknifty": Path("ml/banknifty_model.pkl"),
    "sensex": Path("ml/sensex_model.pkl"),
}

MOVE_CAP = 1.5
NOISE = 0.05


def clamp(x, low, high):
    return max(low, min(x, high))


def normalize_probs(probs):
    total = sum(probs.values())
    if total == 0:
        return {"Bearish": 33, "Sideways": 34, "Bullish": 33}
    return {k: round((v / total) * 100, 2) for k, v in probs.items()}


@lru_cache(maxsize=None)
def load_model(key):
    path = MODEL_PATHS.get(key)
    if path and path.exists():
        return joblib.load(path)
    return None


# =====================================
# ML PREDICTION
# =====================================

def ml_prediction(key, symbol):

    model = load_model(key)
    if model is None:
        return None

    try:
        row = latest_model_features(symbol)
    except Exception as exc:
        print(f"ML feature error [{key}]: {exc}")
        return None

    if row is None or row.empty:
        return None

    X = row.drop(columns=["Target", "NEXT_DAY_RETURN"], errors="ignore")
    X = X.reindex(columns=model.get_booster().feature_names, fill_value=0)

    pred = int(model.predict(X)[0])
    probs = model.predict_proba(X)[0]

    bearish, sideways, bullish = probs

    sentiment = CLASSES[pred]
    strength = bullish - bearish

    if sentiment == "Sideways":
        move = clamp(strength * 15, -0.3, 0.3)
    elif sentiment == "Bullish":
        move = clamp(abs(strength * 100), 0.2, MOVE_CAP)
    else:
        move = clamp(-abs(strength * 100), -MOVE_CAP, -0.2)

    if abs(move) < NOISE:
        move = round(move, 2)

    return {
        "sentiment": sentiment,
        "confidence": round(max(probs) * 100, 2),
        "move": round(move, 2),
        "probabilities": normalize_probs({
            "Bearish": bearish,
            "Sideways": sideways,
            "Bullish": bullish,
        }),
    }


# =====================================
# BLEND ML + GLOBAL + FII/DII
# =====================================

def blend(ml, global_sig, fii_dii, beta):
    """ML + global markets dominate; FII/DII is a small nudge (demo data is not live)."""
    global_move = global_sig["expected_move_pct"] * beta
    # Small move adjustment only — avoids random demo FII flipping the whole call
    fii_nudge = fii_dii["score"] * 0.15
    use_fii_sentiment = fii_dii.get("source") == "live" and abs(fii_dii["score"]) > 0.75

    if ml is None:
        move = clamp(global_move + fii_nudge, -MOVE_CAP, MOVE_CAP)
        sentiment = (
            fii_dii["sentiment"] if use_fii_sentiment else global_sig["sentiment"]
        )
        return {
            "sentiment": sentiment,
            "confidence": global_sig["confidence"],
            "move": round(move, 2),
            "probabilities": global_sig.get("probabilities", {}),
        }

    move = ml["move"] * 0.6 + global_move * 0.35 + fii_nudge * 0.05
    sentiment = fii_dii["sentiment"] if use_fii_sentiment else ml["sentiment"]

    move = clamp(move, -MOVE_CAP, MOVE_CAP)
    if abs(move) < NOISE:
        move = round(move, 2)

    return {
        "sentiment": sentiment,
        "confidence": ml["confidence"],
        "move": round(move, 2),
        "probabilities": ml["probabilities"],
    }


def _index_status(key: str, meta: dict, snap: dict) -> tuple[str, str]:
    if snap.get("data_source") == "proxied_from_nifty":
        return "proxied", "Global + FII/DII (Fin Nifty proxied from NIFTY)"
    if float(snap.get("current", 0) or 0) <= 0:
        return "price_unavailable", "Price unavailable — check Yahoo or manual mode"
    if load_model(key) is not None:
        return "live", f"ML + global + FII/DII ({meta['name']})"
    return "live", f"Global + FII/DII only ({meta['name']})"


# =====================================
# MAIN FUNCTION
# =====================================

def predict_india(investor_snapshots, india_indices):

    global_sig = compute_pre_india_signal(investor_snapshots)
    fii_dii = get_fii_dii_signal()
    country_impact = build_country_impact_analysis()
    index_trade_summary = build_index_trade_summary(global_sig, fii_dii)
    stock_ideas = build_stock_ideas(limit=5)

    indices_out = []

    for key, meta in INDIA_INDICES.items():

        snap = india_indices.get(key, {})
        price = float(snap.get("current", 0) or 0)
        beta = INDEX_MOVE_BETA.get(key, 1.0)
        symbol = meta.get("symbol", "^NSEI")

        if key == "finnifty" or not meta.get("fetch_live", True):
            ml = None
        else:
            ml = ml_prediction(key, symbol)

        core_data = blend(ml, global_sig, fii_dii, beta)
        move = core_data["move"]
        data_status, model_scope = _index_status(key, meta, snap)

        strategy = get_option_strategy(meta["name"], price, core_data["sentiment"], move)
        risk = get_risk_plan(strategy)
        entry = get_entry_plan(core_data["sentiment"], move)

        indices_out.append({
            "index": meta["name"],
            "key": key,
            "sentiment": core_data["sentiment"],
            "confidence": core_data["confidence"],
            "expectedMove": move,
            "expectedPoints": round((move / 100) * price, 2) if price else 0,
            "currentPrice": price,
            "probabilities": core_data["probabilities"],
            "strategy": strategy,
            "risk": risk,
            "entry": entry,
            "dataStatus": data_status,
            "modelScope": model_scope,
            "options_hint": global_sig.get("options_hint", ""),
        })

    nifty = next((i for i in indices_out if i["key"] == "nifty"), None)

    core = {
        "sentiment": nifty["sentiment"] if nifty else "Sideways",
        "confidence": nifty["confidence"] if nifty else 0,
        "expected_move_pct": nifty["expectedMove"] if nifty else 0,
        "probabilities": nifty["probabilities"] if nifty else {},
        "options_hint": global_sig.get("options_hint", ""),
        "source": "ml+global+fii",
    }

    return {
        "core": core,
        "indices": indices_out,
        "global_signal": global_sig,
        "fii_dii": fii_dii,
        "country_impact": country_impact,
        "index_trade_summary": index_trade_summary,
        "stock_ideas": stock_ideas,
    }


# =====================================
# BACKWARD SUPPORT
# =====================================

def predict_all_indices(market_data, technical_data=None):

    investor_keys = {
        "japan", "singapore", "uae", "united_states",
        "canada", "united_kingdom", "norway",
    }

    investor = {k: market_data[k] for k in investor_keys if k in market_data}

    india = {
        k: market_data[k]
        for k in ("nifty", "banknifty", "finnifty", "sensex")
        if k in market_data
    }

    return predict_india(investor, india)["indices"]
