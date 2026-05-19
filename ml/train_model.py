import pandas as pd
import joblib

from xgboost import XGBClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import TimeSeriesSplit

print("Loading dataset...")

df = pd.read_csv("historical_data/dataset.csv")

# =====================================
# CLEAN DATA
# =====================================

df = df.dropna()

# REMOVE NON-NUMERIC
df = df.select_dtypes(include=["float64", "int64"])

# =====================================
# FEATURES
# =====================================

# Drop target and same-day return (leakage: Target is derived from RETURN)
drop = [c for c in ("Target", "RETURN") if c in df.columns]
X = df.drop(columns=drop)
y = df["Target"]

# =====================================
# TIME SERIES SPLIT
# =====================================

tscv = TimeSeriesSplit(n_splits=5)

for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

# =====================================
# MODEL
# =====================================

model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
)

print("Training model...")
model.fit(X_train, y_train)

# =====================================
# EVALUATION
# =====================================

preds = model.predict(X_test)

print("\nClassification Report:\n")
print(classification_report(y_test, preds))

# =====================================
# SAVE
# =====================================

joblib.dump(model, "ml/nifty_model.pkl")

print("Model saved!")