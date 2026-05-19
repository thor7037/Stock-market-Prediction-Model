"""Indian Market AI — global lead markets + options-oriented India predictions."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from indicators.technical_indicators import get_technical_indicators
from prediction.predictor import predict_india
from services.global_markets import INVESTOR_MARKETS, markets_table_rows
from services.market_fetcher import (
    fetch_india_indices,
    fetch_investor_markets,
    snapshot_from_manual,
)
from utils.streamlit_ui import inject_css, render_prediction_card

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Indian Market AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

REFRESH_TTL = 300  # seconds


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_auto_investor_markets() -> dict:
    return fetch_investor_markets()


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_auto_india_indices() -> dict:
    return fetch_india_indices()


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_technicals() -> dict:
    return get_technical_indicators()


def _manual_snapshots() -> dict[str, dict]:
    out = {}
    for m in INVESTOR_MARKETS:
        with st.sidebar.expander(m.country, expanded=False):
            use_pct = st.checkbox("Use % change only", key=f"pct_{m.key}")
            high = st.number_input("High", key=f"h_{m.key}", value=0.0, format="%.2f")
            low = st.number_input("Low", key=f"l_{m.key}", value=0.0, format="%.2f")
            close = st.number_input("Close", key=f"c_{m.key}", value=0.0, format="%.2f")
            pct = st.number_input("Day % change", key=f"p_{m.key}", value=0.0, format="%.2f")

        if close > 0 and high > 0 and low > 0:
            out[m.key] = snapshot_from_manual(
                high=high,
                low=low,
                close=close,
                percentage=pct if use_pct else None,
            )
        elif use_pct and pct != 0:
            out[m.key] = snapshot_from_manual(
                high=close * 1.005,
                low=close * 0.995,
                close=close or 1.0,
                percentage=pct,
            )
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

st.sidebar.title("Controls")
data_mode = st.sidebar.radio(
    "Market data source",
    ["Auto (Yahoo Finance)", "Manual high / low"],
    index=0,
)

if st.sidebar.button("Refresh data", width="stretch"):
    st.cache_data.clear()

manual_snapshots = _manual_snapshots() if data_mode.startswith("Manual") else {}

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────

with st.spinner("Loading markets…"):
    if data_mode.startswith("Manual") and manual_snapshots:
        investor = load_auto_investor_markets()
        investor.update(manual_snapshots)
        india = load_auto_india_indices()
    elif data_mode.startswith("Manual"):
        st.sidebar.warning("Enter at least Close + High + Low for one market.")
        investor = load_auto_investor_markets()
        india = load_auto_india_indices()
    else:
        investor = load_auto_investor_markets()
        india = load_auto_india_indices()

    technicals = load_technicals()
    prediction = predict_india(investor, india)

nifty_ok = float(india.get("nifty", {}).get("current") or 0) > 0
if not nifty_ok:
    st.warning(
        "**Live market data unavailable** (Yahoo Finance could not be reached or returned empty). "
        "Check internet / DNS (e.g. `query1.finance.yahoo.com`), VPN, or firewall. "
        "Use **Manual high / low** in the sidebar to enter global levels and still get a bias signal."
    )

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.title("Indian Market AI")
st.caption(
    "Pre-India global signal → NIFTY / Bank Nifty direction & move size for options planning"
)

core = prediction["core"]
global_sig = prediction["global_signal"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Global composite", f"{global_sig['composite_score']:.2f}")
m2.metric("India bias", core["sentiment"])
m3.metric("Confidence", f"{core['confidence']}%")
m4.metric("Expected move (NIFTY)", f"±{core['expected_move_pct']}%")

st.info(f"**Options playbook:** {core.get('options_hint', global_sig['options_hint'])}")

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────

tab_global, tab_tech, tab_predict, tab_reference = st.tabs(
    ["Global lead markets", "India technicals", "AI predictions", "Reference"]
)

with tab_global:
    st.subheader("International markets (before / into India session)")

    st.dataframe(
        pd.DataFrame(markets_table_rows()),
        width="stretch",
        hide_index=True,
    )

    st.divider()
    cols = st.columns(2)

    for i, market in enumerate(INVESTOR_MARKETS):
        snap = investor.get(market.key, {})
        with cols[i % 2]:
            st.metric(
                f"{market.country} — {market.market_name}",
                snap.get("current", "—"),
                f"{snap.get('percentage', 0)}% · range {snap.get('range_pct', 0)}%",
            )
            st.caption(
                f"IST {market.open_ist}–{market.close_ist} · "
                f"Impact ~{market.impact_pct}% · {market.notes}"
            )

    if global_sig.get("breakdown"):
        st.subheader("Weighted contribution to India bias")
        st.dataframe(
            pd.DataFrame(global_sig["breakdown"]),
            width="stretch",
            hide_index=True,
        )

with tab_tech:
    st.subheader("NIFTY technicals")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSI", technicals["rsi"])
    c2.metric("EMA 20", technicals["ema20"])
    c3.metric("MACD", technicals["macd"])
    c4.metric("NIFTY spot", technicals["current_price"])

with tab_predict:
    st.subheader("Index predictions (options-oriented)")
    st.caption(f"Model source: {core.get('source', 'n/a')}")

    left, right = st.columns(2)
    for i, pred in enumerate(prediction["indices"]):
        with (left if i % 2 == 0 else right):
            render_prediction_card(pred)

with tab_reference:
    st.markdown(
        """
        ### How to use manual mode
        1. After global markets close (especially **US** and **Japan**), enter **High**, **Low**, **Close** per country.  
        2. Or tick **Use % change only** and enter the day’s percentage move.  
        3. Open **AI predictions** for India direction and suggested options bias.

        ### Disclaimer
        This tool is for research and education only. Not financial advice.  
        Options involve substantial risk; validate signals with your own rules and risk management.
        """
    )

st.sidebar.divider()
st.sidebar.caption(f"Cache TTL: {REFRESH_TTL}s · Retrain: `python ml/dataset_builder.py && python ml/train_model.py`")
