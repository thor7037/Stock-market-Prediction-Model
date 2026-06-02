"""Global market comparison charts."""

import pandas as pd
import plotly.express as px


def global_market_chart(symbols: list[str]):
    df = pd.DataFrame({"Symbol": symbols, "Change %": [0.0] * len(symbols)})
    return px.bar(df, x="Symbol", y="Change %", title="Global Markets")
