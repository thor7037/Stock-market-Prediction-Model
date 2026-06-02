"""News scraping and sentiment analysis."""


def get_market_sentiment(symbol: str | None = None):
    return {
        "symbol": symbol,
        "label": "Neutral",
        "score": 0.0,
        "items": [],
        "source": "not_configured",
    }
