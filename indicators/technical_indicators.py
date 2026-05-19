import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

from services.yf_helpers import DEFAULT_PERIODS_LONG, download_daily, flatten_columns


def get_technical_indicators():
    try:
        df = download_daily("^NSEI", periods=DEFAULT_PERIODS_LONG)
        df = flatten_columns(df)

        if df is None or df.empty or len(df) < 30:
            return {
                "rsi": 0,
                "ema20": 0,
                "macd": 0,
                "current_price": 0,
            }

        close = df["Close"].squeeze()

        rsi = RSIIndicator(close=close).rsi().iloc[-1]
        ema20 = EMAIndicator(close=close, window=20).ema_indicator().iloc[-1]
        macd = MACD(close=close).macd().iloc[-1]
        price = close.iloc[-1]

        return {
            "rsi": round(float(rsi), 2),
            "ema20": round(float(ema20), 2),
            "macd": round(float(macd), 2),
            "current_price": round(float(price), 2),
        }

    except Exception as e:
        print("TECHNICAL ERROR:", e)

        return {
            "rsi": 0,
            "ema20": 0,
            "macd": 0,
            "current_price": 0,
        }
