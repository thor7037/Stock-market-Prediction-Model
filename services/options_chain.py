"""Options chain data for indices and equities."""


def get_options_chain(symbol: str):
    return {
        "symbol": symbol,
        "calls": [],
        "puts": [],
        "source": "not_configured",
    }
