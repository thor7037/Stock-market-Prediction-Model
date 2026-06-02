"""
International markets that lead Indian session (FII / regional flow).
Impact weights are priors — refine with ml/global_feature_builder.py regression.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GlobalMarket:
    key: str
    country: str
    market_name: str
    symbol: str
    open_ist: str
    close_ist: str
    impact_pct: float
    notes: str = ""
    symbol_alternates: tuple[str, ...] = ()


# Ordered by typical pre-India relevance (IST session windows are approximate; US shifts with DST).
INVESTOR_MARKETS: tuple[GlobalMarket, ...] = (
    GlobalMarket(
        key="japan",
        country="Japan",
        market_name="Nikkei 225 (TSE)",
        symbol="^N225",
        open_ist="05:30",
        close_ist="11:30",
        impact_pct=12.0,
        notes="Asia risk sentiment before NSE open",
        symbol_alternates=("EWJ",),
    ),
    GlobalMarket(
        key="singapore",
        country="Singapore",
        market_name="STI / SGX (GIFT Nifty proxy)",
        symbol="^STI",
        open_ist="06:40",
        close_ist="15:00",
        impact_pct=22.0,
        notes="Strong India lead via SGX / GIFT Nifty",
        symbol_alternates=("ES3.SI",),
    ),
    GlobalMarket(
        key="uae",
        country="United Arab Emirates",
        market_name="DFM General Index",
        symbol="DFMGI.AE",
        open_ist="07:00",
        close_ist="15:30",
        impact_pct=4.0,
        notes="Regional flows; verify symbol on yfinance",
        symbol_alternates=("ADX.AD",),
    ),
    GlobalMarket(
        key="united_states",
        country="United States",
        market_name="S&P 500",
        symbol="^GSPC",
        open_ist="19:00",
        close_ist="01:30",
        impact_pct=38.0,
        notes="Largest FII bloc; prior close drives India gap",
    ),
    GlobalMarket(
        key="canada",
        country="Canada",
        market_name="S&P/TSX Composite",
        symbol="^GSPTSE",
        open_ist="19:00",
        close_ist="01:30",
        impact_pct=6.0,
        notes="Correlated with US overnight risk",
    ),
    GlobalMarket(
        key="united_kingdom",
        country="United Kingdom",
        market_name="FTSE 100",
        symbol="^FTSE",
        open_ist="13:30",
        close_ist="22:00",
        impact_pct=10.0,
        notes="European FII; overlaps India afternoon",
    ),
    GlobalMarket(
        key="norway",
        country="Norway",
        market_name="OSEBX All-Share",
        symbol="^OSEAX",
        open_ist="13:30",
        close_ist="22:00",
        impact_pct=3.0,
        notes="Indirect via energy / Europe",
    ),
)

MARKET_BY_KEY = {m.key: m for m in INVESTOR_MARKETS}

# Fin Nifty spot is proxied from NIFTY (Yahoo has no reliable FIN NIFTY ticker).
FINNIFTY_PROXY_RATIO = 0.92

INDIA_INDICES = {
    "nifty": {
        "name": "NIFTY 50",
        "symbol": "^NSEI",
        "symbol_alternates": (),
        "fetch_live": True,
        "proxy_from": None,
    },
    "banknifty": {
        "name": "BANK NIFTY",
        "symbol": "^NSEBANK",
        "symbol_alternates": (),
        "fetch_live": True,
        "proxy_from": None,
    },
    "finnifty": {
        "name": "FIN NIFTY",
        "symbol": "^CNXFIN",
        "symbol_alternates": (),
        "fetch_live": False,
        "proxy_from": "nifty",
    },
    "sensex": {
        "name": "SENSEX",
        "symbol": "^BSESN",
        "symbol_alternates": (),
        "fetch_live": True,
        "proxy_from": None,
    },
}

# Rough beta vs NIFTY for scaling expected move to other indices
INDEX_MOVE_BETA = {
    "nifty": 1.0,
    "banknifty": 1.35,
    "finnifty": 1.15,
    "sensex": 1.0,
}


def markets_table_rows() -> list[dict[str, Any]]:
    return [
        {
            "Country": m.country,
            "Market": m.market_name,
            "Open (IST)": m.open_ist,
            "Close (IST)": m.close_ist,
            "India impact %": m.impact_pct,
            "Symbol": m.symbol,
        }
        for m in INVESTOR_MARKETS
    ]
