"""Candlestick chart rendering."""

import plotly.graph_objects as go


def candlestick_chart(ohlcv, title: str = ""):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=ohlcv.index,
                open=ohlcv["Open"],
                high=ohlcv["High"],
                low=ohlcv["Low"],
                close=ohlcv["Close"],
            )
        ]
    )
    fig.update_layout(title=title)
    return fig
