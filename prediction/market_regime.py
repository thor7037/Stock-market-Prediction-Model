"""Market regime detection (trending, ranging, volatile)."""


def detect_regime(ohlcv):
    if ohlcv is None or ohlcv.empty or len(ohlcv) < 20:
        return "neutral"

    close = ohlcv["Close"]
    high = ohlcv["High"]
    low = ohlcv["Low"]

    recent_return = abs((close.iloc[-1] / close.iloc[-20]) - 1)
    avg_range = ((high - low) / close).tail(20).mean()

    if avg_range > 0.025:
        return "volatile"
    if recent_return > 0.04:
        return "trending"
    return "ranging"
