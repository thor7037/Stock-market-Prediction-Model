"""Train multi-class index direction models with stronger trend validation."""

from __future__ import annotations

from collections import Counter

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

MODEL_NAMES = ("nifty", "banknifty", "sensex")


def _prepare_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    if "Target" not in df.columns:
        raise ValueError("Dataset must contain Target")

    drop = [
        "Target",
        "NEXT_DAY_RETURN",
        "ABS_NEXT_DAY_RETURN",
        "Date",
        "Direction",
    ]
    X = df.drop(columns=[c for c in drop if c in df.columns])
    X = X.select_dtypes(include=["float64", "int64"])
    y = df["Target"].astype(int)
    return X, y


def _sample_weights(y: pd.Series) -> pd.Series:
    counts = Counter(int(v) for v in y)
    total = len(y)
    class_weights = {
        cls: total / (len(counts) * count)
        for cls, count in counts.items()
        if count > 0
    }
    return y.map(lambda label: class_weights[int(label)])


def train_model(name: str) -> None:
    print(f"\nTraining {name.upper()} model...")

    df = pd.read_csv(f"historical_data/{name}.csv")
    df = df.dropna().reset_index(drop=True)

    X, y = _prepare_xy(df)

    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        shuffle=False,
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval,
        y_trainval,
        test_size=0.2,
        shuffle=False,
    )

    model = XGBClassifier(
        n_estimators=1200,
        max_depth=4,
        learning_rate=0.02,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=5,
        gamma=0.1,
        reg_alpha=0.2,
        reg_lambda=1.2,
        objective="multi:softprob",
        eval_metric="mlogloss",
        tree_method="hist",
        random_state=42,
        n_jobs=1,
    )

    weights_train = _sample_weights(y_train)

    model.fit(
        X_train,
        y_train,
        sample_weight=weights_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
        early_stopping_rounds=80,
    )

    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)

    print(f"\nTest accuracy: {accuracy * 100:.2f}%")
    print("\nClassification report:")
    print(classification_report(y_test, preds, digits=4, zero_division=0))

    print("Confusion matrix:")
    print(confusion_matrix(y_test, preds))

    print(f"\nRetraining {name.upper()} model on train+validation data...")
    final_weights = _sample_weights(y_trainval)
    model.fit(
        X_trainval,
        y_trainval,
        sample_weight=final_weights,
        verbose=False,
    )

    joblib.dump(model, f"ml/{name}_model.pkl")
    print(f"Saved model to ml/{name}_model.pkl")


if __name__ == "__main__":
    for model_name in MODEL_NAMES:
        train_model(model_name)
