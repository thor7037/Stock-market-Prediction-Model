"""Streamlit UI helpers."""

from __future__ import annotations

import streamlit as st

SENTIMENT_COLORS = {
    "Bullish": "#22C55E",
    "Bearish": "#EF4444",
    "Sideways": "#FACC15",
    "Unknown": "#9CA3AF",
}


def _fmt_strategy(strategy: dict) -> str:
    if not strategy:
        return ""
    name = strategy.get("strategy", "")
    if name == "No data":
        return "Strategy: awaiting price data"
    parts = [f"**{name}**"]
    for label, key in (
        ("CE", "strike"),
        ("Buy CE", "buy_ce"),
        ("Sell CE", "sell_ce"),
        ("Buy PE", "buy_pe"),
        ("Sell PE", "sell_pe"),
    ):
        if key in strategy:
            parts.append(f"{label}: {strategy[key]}")
    return " · ".join(parts)


def _fmt_risk(risk: dict) -> str:
    if not risk:
        return ""
    return (
        f"Type: {risk.get('type', '—')} · "
        f"Risk: ₹{risk.get('riskAmount', 0)} · "
        f"SL: {risk.get('stopLoss', '—')} · "
        f"Target: {risk.get('target', '—')} · "
        f"Lots: {risk.get('lotSize', '—')}"
    )


def _fmt_entry(entry: dict) -> str:
    if not entry:
        return ""
    return f"Entry: **{entry.get('action', '—')}** — {entry.get('reason', '')}"


def render_prediction_card(pred: dict) -> None:
    color = SENTIMENT_COLORS.get(pred["sentiment"], "#9CA3AF")
    probs = pred.get("probabilities", {})
    hint = pred.get("options_hint", "")
    model_scope = pred.get("modelScope", "")
    data_status = pred.get("dataStatus", "live")
    move = float(pred.get("expectedMove", 0) or 0)
    points = float(pred.get("expectedPoints", 0) or 0)
    move_text = "0.00%" if move == 0 else f"{move:+.2f}%"
    points_text = "0.00" if points == 0 else f"{points:+.2f}"

    status_map = {
        "price_unavailable": "Price unavailable",
        "proxied": "Spot proxied from NIFTY (Yahoo has no Fin Nifty ticker)",
    }
    status_text = status_map.get(data_status, "")

    strategy = pred.get("strategy", {})
    risk = pred.get("risk", {})
    entry = pred.get("entry", {})

    st.markdown(
        f"""
        <div style="display:block;background:#111827;padding:22px;border-radius:16px;border:1px solid #1f2937;margin-bottom:12px;">
        <h3 style="color:#f9fafb;margin:0 0 8px 0;">{pred['index']}</h3>
        <h1 style="color:{color};margin:0 0 6px 0;">{pred['sentiment']}</h1>
        {"<p style='color:#93c5fd;font-size:0.8rem;margin:0 0 10px 0;'>" + model_scope + "</p>" if model_scope else ""}
        <p style="color:#22D3EE;margin:4px 0;">Confidence: {pred['confidence']}%</p>
        <p style="color:#9ca3af;margin:4px 0;">Spot: {pred['currentPrice']}</p>
        {"<p style='color:#fbbf24;font-size:0.85rem;margin:4px 0;'>" + status_text + "</p>" if status_text else ""}
        <p style="color:#f3f4f6;margin:4px 0;">
            Expected: {move_text} ({points_text} pts)
        </p>
        <p style="color:#9ca3af;font-size:0.9rem;margin:8px 0 0 0;">
            Bearish {probs.get('Bearish', 0)}% ·
            Sideways {probs.get('Sideways', 0)}% ·
            Bullish {probs.get('Bullish', 0)}%
        </p>
        {"<p style='color:#a5b4fc;font-size:0.85rem;margin-top:10px;'>" + hint + "</p>" if hint else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if strategy or risk or entry:
        with st.expander(f"Options plan — {pred['index']}", expanded=False):
            if strategy:
                st.markdown(_fmt_strategy(strategy))
            if risk:
                st.caption(_fmt_risk(risk))
            if entry:
                st.caption(_fmt_entry(entry))


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; }
        div[data-testid="stMetric"] {
            background: #111827;
            padding: 12px;
            border-radius: 12px;
            border: 1px solid #1f2937;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
