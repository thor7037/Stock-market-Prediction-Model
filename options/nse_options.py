"""NSE option-chain helpers."""

from __future__ import annotations


def fetch_nse_option_chain(symbol: str = "NIFTY") -> dict:
    try:
        from nsepython import nse_optionchain_scrapper
    except ImportError:
        return {
            "symbol": symbol,
            "records": {},
            "source": "nsepython_missing",
        }

    try:
        data = nse_optionchain_scrapper(symbol)
    except Exception as exc:
        return {
            "symbol": symbol,
            "records": {},
            "error": str(exc),
            "source": "nsepython",
        }

    return {
        "symbol": symbol,
        "records": data,
        "source": "nsepython",
    }


if __name__ == "__main__":
    print(fetch_nse_option_chain())
