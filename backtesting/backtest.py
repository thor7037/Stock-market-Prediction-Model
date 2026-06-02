import pandas as pd


def run_backtest(df):

    capital = 100000

    trades = []

    for i in range(len(df) - 1):

        signal = df.iloc[i]["Prediction"]

        today_close = df.iloc[i]["Close"]
        next_close = df.iloc[i + 1]["Close"]

        pnl = 0

        if signal == "Bullish":
            pnl = next_close - today_close

        elif signal == "Bearish":
            pnl = today_close - next_close

        capital += pnl

        trades.append(
            {
                "Date": df.iloc[i]["Date"],
                "Signal": signal,
                "PnL": round(pnl, 2),
                "Capital": round(capital, 2),
            }
        )

    return pd.DataFrame(trades)