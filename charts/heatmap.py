"""Heatmap visualizations."""

import pandas as pd
import plotly.express as px


def sector_heatmap(data):
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame({"Sector": ["N/A"], "Change %": [0.0]})
    return px.density_heatmap(df, x=df.columns[0], y=df.columns[-1], title="Sector Heatmap")
