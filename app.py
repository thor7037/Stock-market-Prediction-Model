"""Indian Market AI — global lead markets + options-oriented India predictions."""

from __future__ import annotations

import json

import streamlit as st
import pandas as pd

from indicators.technical_indicators import get_technical_indicators
from ml.feature_utils import clear_feature_cache
from prediction.predictor import predict_india
from services.global_markets import INVESTOR_MARKETS, markets_table_rows
from services.market_fetcher import (
    fetch_india_indices,
    fetch_investor_markets,
    safe_fetch_ohlc,
    snapshot_from_manual,
)
from services.fii_dii import clear_fii_dii_cache
from services.yf_helpers import clear_failed_symbols
from utils.streamlit_ui import inject_css, render_prediction_card

st.set_page_config(
    page_title="Indian Market AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

REFRESH_TTL = 300


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_auto_investor_markets() -> dict:
    return fetch_investor_markets()


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_auto_india_indices() -> dict:
    return fetch_india_indices()


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_technicals() -> dict:
    return get_technical_indicators()


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_india_vix() -> dict:
    return safe_fetch_ohlc("^INDIAVIX") or {}


@st.cache_data(ttl=REFRESH_TTL, show_spinner=False)
def load_prediction(investor_json: str, india_json: str) -> dict:
    """Cache full prediction so reruns / sidebar widgets do not reshuffle signals."""
    investor = json.loads(investor_json)
    india = json.loads(india_json)
    return predict_india(investor, india)


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


def _all_investor_markets_manual(manual: dict) -> bool:
    return len(manual) >= len(INVESTOR_MARKETS)


# ── Sidebar ──────────────────────────────────────────────────────────────────

st.sidebar.title("Controls")
data_mode = st.sidebar.radio(
    "Market data source",
    ["Auto (Yahoo Finance)", "Manual high / low"],
    index=0,
)

if st.sidebar.button("Refresh data", width="stretch"):
    st.cache_data.clear()
    clear_failed_symbols()
    clear_feature_cache()
    clear_fii_dii_cache()

manual_snapshots = _manual_snapshots() if data_mode.startswith("Manual") else {}

# ── Load data ────────────────────────────────────────────────────────────────

with st.spinner("Loading markets…"):
    if data_mode.startswith("Manual") and _all_investor_markets_manual(manual_snapshots):
        investor = manual_snapshots
        india = load_auto_india_indices()
    elif data_mode.startswith("Manual") and manual_snapshots:
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
    vix_snap = load_india_vix()
    prediction = load_prediction(
        json.dumps(investor, sort_keys=True, default=str),
        json.dumps(india, sort_keys=True, default=str),
    )

fii_dii = prediction.get("fii_dii", {})
core = prediction["core"]
global_sig = prediction["global_signal"]
country_impact = prediction.get("country_impact", [])
index_trade_summary = prediction.get("index_trade_summary", {})
stock_ideas = prediction.get("stock_ideas", [])

nifty_ok = float(india.get("nifty", {}).get("current") or 0) > 0
if not nifty_ok:
    st.warning(
        "**Live market data unavailable.** Check internet/DNS or use **Manual high / low** "
        "in the sidebar for global markets."
    )

# ── Header ───────────────────────────────────────────────────────────────────

st.title("Indian Market AI")
st.caption("Pre-India global signal + FII/DII → India index direction for options planning")

st.subheader("Institutional flow (FII / DII)")
if fii_dii.get("source") == "demo_daily":
    st.caption(
        f"Demo flow for **{fii_dii.get('trading_day', 'today')}** — stable until you click "
        "**Refresh data** or the next trading day. Not live NSE data."
    )
f1, f2, f3, f4 = st.columns(4)
f1.metric("FII", f"₹{fii_dii.get('fii', 0):,} Cr")
f2.metric("DII", f"₹{fii_dii.get('dii', 0):,} Cr")
f3.metric("Net", f"₹{fii_dii.get('net', 0):,} Cr")
f4.metric("Flow score", fii_dii.get("score", 0))
f5, = st.columns(1)
f5.metric("Flow bias (demo)", fii_dii.get("sentiment", "N/A"))

st.subheader("Quick global snapshot")
g1, g2, g3, g4 = st.columns(4)
g1.metric(
    "US (S&P 500)",
    investor.get("united_states", {}).get("current", "—"),
    f"{investor.get('united_states', {}).get('percentage', 0)}%",
)
g2.metric(
    "Japan (Nikkei)",
    investor.get("japan", {}).get("current", "—"),
    f"{investor.get('japan', {}).get('percentage', 0)}%",
)
g3.metric(
    "Singapore (STI)",
    investor.get("singapore", {}).get("current", "—"),
    f"{investor.get('singapore', {}).get('percentage', 0)}%",
)
g4.metric(
    "India VIX",
    vix_snap.get("current", "—"),
    f"{vix_snap.get('percentage', 0)}%",
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Global composite", f"{global_sig['composite_score']:.2f}")
m2.metric("India bias", core["sentiment"])
m3.metric("Confidence", f"{core['confidence']}%")
expected_move = float(core["expected_move_pct"])
expected_move_text = "0.00%" if expected_move == 0 else f"{expected_move:+.2f}%"
m4.metric("Expected move (NIFTY)", expected_move_text)

st.info(f"**Options playbook:** {core.get('options_hint', global_sig.get('options_hint', ''))}")

# ── Original tabs (restored) ───────────────────────────────────────────────────

tab_global, tab_tech, tab_predict, tab_trade, tab_reference = st.tabs(
    ["Global lead markets", "India technicals", "AI predictions", "Trade ideas", "Reference"]
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

with tab_trade:
    st.subheader("Country impact analysis")
    if country_impact:
        st.dataframe(
            pd.DataFrame(country_impact),
            width="stretch",
            hide_index=True,
        )
    st.divider()
    st.subheader("Index trade summary")
    st.json(index_trade_summary)
    st.divider()
    st.subheader("Best intraday stock ideas")
    if stock_ideas:
        st.dataframe(
            pd.DataFrame(stock_ideas),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No stock ideas available right now.")

with tab_reference:
    st.markdown(
        """
        ### How to use manual mode
        1. After global markets close (especially **US** and **Japan**), enter **High**, **Low**, **Close** per country.
        2. Or tick **Use % change only** and enter the day's percentage move.
        3. Open **AI predictions** for direction, strategy, risk, and entry timing.

        ### Fin Nifty
        Yahoo has no reliable Fin Nifty ticker — spot is **estimated from NIFTY**.

        ### FII / DII
        Demo flow is **fixed for the calendar day** (same after refresh within the session cache).
        Click **Refresh data** to reload market + prediction caches. Live NSE feed can be added later.

        ### Disclaimer
        Research and education only. Not financial advice. Options involve substantial risk.
        """
    )

st.sidebar.divider()
st.sidebar.caption(
    f"Cache TTL: {REFRESH_TTL}s · Retrain: "
    "`python ml/dataset_builder.py && python ml/train_model.py`"
)
