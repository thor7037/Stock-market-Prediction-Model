"""Streamlit UI helpers."""

from __future__ import annotations

import streamlit as st

SENTIMENT_COLORS = {
    "Bullish": "#22C55E",
    "Bearish": "#EF4444",
    "Sideways": "#FACC15",
    "Unknown": "#9CA3AF",
}


def render_prediction_card(pred: dict) -> None:
    color = SENTIMENT_COLORS.get(pred["sentiment"], "#9CA3AF")
    probs = pred.get("probabilities", {})
    hint = pred.get("options_hint", "")

    st.markdown(
        f"""
        <div style="display:block;background:#111827;padding:22px;border-radius:16px;border:1px solid #1f2937;margin-bottom:12px;">
        <h3 style="color:#f9fafb;margin:0 0 8px 0;">{pred['index']}</h3>
        <h1 style="color:{color};margin:0 0 6px 0;">{pred['sentiment']}</h1>
        <p style="color:#22D3EE;margin:4px 0;">Confidence: {pred['confidence']}%</p>
        <p style="color:#9ca3af;margin:4px 0;">Spot: {pred['currentPrice']}</p>
        <p style="color:#f3f4f6;margin:4px 0;">
            Expected: {pred['expectedMove']}% ({pred['expectedPoints']} pts)
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
