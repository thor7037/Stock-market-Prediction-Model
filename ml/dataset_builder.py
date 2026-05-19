import pandas as pd
import yfinance as yf

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange

# =====================================
# DOWNLOAD
# =====================================

def download(symbol):

    df = yf.download(
        symbol,
        start="2015-01-01",
        progress=False
    )

    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # rename properly
    df.columns = ["Open", "High", "Low", "Close", "Volume"]

    return df

# =====================================
# BUILD DATASET
# =====================================

def build_dataset():

    print("Downloading data...")

    nifty = download("^NSEI")
    vix = download("^INDIAVIX")

    df = pd.concat([nifty, vix.add_prefix("VIX_")], axis=1)

    df = df.ffill().dropna()

    # =====================================
    # RETURNS
    # =====================================

    df["RETURN"] = df["Close"].pct_change()

    # =====================================
    # TARGET (FIXED)
    # =====================================

    df["Target"] = 1

    df.loc[df["RETURN"] > 0.005, "Target"] = 2
    df.loc[df["RETURN"] < -0.005, "Target"] = 0

    # =====================================
    # TECHNICALS
    # =====================================

    close = df["Close"].squeeze()

    df["RSI"] = RSIIndicator(close=close).rsi()
    df["EMA20"] = EMAIndicator(close=close, window=20).ema_indicator()
    df["MACD"] = MACD(close=close).macd()

    # =====================================
    # VOLATILITY
    # =====================================

    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )

    df["ATR"] = atr.average_true_range()
    df["RANGE"] = df["High"] - df["Low"]
    df["VIX_CHANGE"] = df["VIX_Close"].pct_change()

    # =====================================
    # MOMENTUM
    # =====================================

    df["MOMENTUM_3"] = df["Close"].pct_change(3)
    df["MOMENTUM_5"] = df["Close"].pct_change(5)

    # =====================================
    # CLEAN
    # =====================================

    df = df.dropna()

    # REMOVE DATE COLUMN ISSUE
    df = df.reset_index(drop=True)

    # =====================================
    # SAVE
    # =====================================

    df.to_csv("historical_data/dataset.csv", index=False)

    print("Dataset ready!")
    print(df.tail())


if __name__ == "__main__":
    build_dataset()