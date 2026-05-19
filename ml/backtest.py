import pandas as pd
import joblib

print("Running backtest...")

df = pd.read_csv("historical_data/dataset.csv")

df = df.dropna()
df = df.select_dtypes(include=["float64", "int64"])

model = joblib.load("ml/nifty_model.pkl")

X = df.drop(columns=["Target"])
y = df["Target"]

preds = model.predict(X)

df["Prediction"] = preds

capital = 100000
profits = []

for i in range(1, len(df)):

    signal = df["Prediction"].iloc[i]
    move = df["RETURN"].iloc[i]

    pnl = 0

    if signal == 2:
        pnl = move * 100000
    elif signal == 0:
        pnl = -move * 100000

    capital += pnl
    profits.append(pnl)

print("\nFinal Capital:", round(capital, 2))
print("Total Trades:", len(profits))