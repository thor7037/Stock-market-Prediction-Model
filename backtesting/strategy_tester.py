"""Strategy testing utilities."""

from typing import Callable


def test_strategy(
    strategy: Callable,
    symbols: list[str],
):
    """
    Execute strategy on multiple symbols.

    Returns:
    {
        "NIFTY": {...},
        "BANKNIFTY": {...}
    }
    """

    results = {}

    for symbol in symbols:

        try:

            signal = strategy(symbol)

            results[symbol] = {
                "success": True,
                "result": signal,
            }

        except Exception as exc:

            results[symbol] = {
                "success": False,
                "error": str(exc),
            }

    return results


# =====================================
# EXAMPLE
# =====================================

if __name__ == "__main__":

    def sample_strategy(symbol):

        return {
            "symbol": symbol,
            "signal": "Bullish",
            "confidence": 72,
        }

    results = test_strategy(
        sample_strategy,
        ["NIFTY", "BANKNIFTY", "SENSEX"]
    )

    from pprint import pprint

    pprint(results)