"""Shared helper utilities."""

from datetime import datetime


def format_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def is_market_hours(now: datetime | None = None) -> bool:
    now = now or datetime.now()
    return now.weekday() < 5 and 9 <= now.hour < 16
