import pandas as pd
from xgboost import XGBClassifier

print("Running backtest...")

DATASET = "historical_data/nifty.csv"
df = pd.read_csv(DATASET)

if "Target" not in df.columns or "NEXT_DAY_RETURN" not in df.columns:
    raise ValueError(f"{DATASET} must contain Target and NEXT_DAY_RETURN")

df = df.dropna()
df = df.select_dtypes(include=["float64", "int64"])

X = df.drop(columns=["Target", "NEXT_DAY_RETURN"], errors="ignore")
y = df["Target"]

split_at = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split_at], X.iloc[split_at:]
y_train = y.iloc[:split_at]
test_df = df.iloc[split_at:].copy()

model = XGBClassifier(
    n_estimators=120,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=1,
)

model.fit(X_train, y_train)

preds = model.predict(X_test)

test_df["Prediction"] = preds

capital = 100000
profits = []

for i in range(len(test_df)):

    signal = test_df["Prediction"].iloc[i]
    move = test_df["NEXT_DAY_RETURN"].iloc[i]

    pnl = 0

    if signal == 2:
        pnl = move * 100000
        profits.append(pnl)
    elif signal == 0:
        pnl = -move * 100000
        profits.append(pnl)

    capital += pnl

print("\nFinal Capital:", round(capital, 2))
print("Total Trades:", len(profits))
