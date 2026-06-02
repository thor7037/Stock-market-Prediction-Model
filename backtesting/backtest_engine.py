import pandas as pd
import yfinance as yf

from backtesting.backtest import run_backtest


# =====================================
# SAMPLE STRATEGY
# =====================================

def strategy(history):

    if len(history) < 20:
        return 0

    sma20 = history["Close"].tail(20).mean()
    current = history["Close"].iloc[-1]

    if current > sma20:
        return 1      # Bullish

    if current < sma20:
        return -1     # Bearish

    return 0


# =====================================
# DOWNLOAD DATA
# =====================================

ohlcv = yf.download(
    "^NSEI",
    start="2023-01-01",
    progress=False,
)

result = run_backtest(
    strategy,
    ohlcv,
    initial_capital=100000,
)

print("\n========== BACKTEST ==========")
print("Initial Capital :", result["initial_capital"])
print("Final Capital   :", result["final_capital"])
print("Trades          :", len(result["trades"]))

if result["trades"]:
    print("\nLast 5 Trades:")
    for trade in result["trades"][-5:]:
        print(trade)