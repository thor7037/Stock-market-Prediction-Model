import sqlite3

from datetime import datetime

# =====================================
# CREATE DATABASE
# =====================================

def create_database():

    conn = sqlite3.connect(
        "database/market_data.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS market_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT,

            nasdaq REAL,
            dow REAL,
            sp500 REAL,

            nikkei REAL,
            hangseng REAL,

            crude REAL,
            dxy REAL,
            vix REAL,

            nifty REAL,

            nifty_prediction REAL,

            expected_points REAL
        )
        """
    )

    conn.commit()

    conn.close()

# =====================================
# SAVE MARKET DATA
# =====================================

def save_market_data(
    market_data,
    prediction,
):
    nifty_data = market_data.get("giftNifty") or market_data.get("nifty") or {}

    conn = sqlite3.connect(
        "database/market_data.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO market_history (

            timestamp,

            nasdaq,
            dow,
            sp500,

            nikkei,
            hangseng,

            crude,
            dxy,
            vix,

            nifty,

            nifty_prediction,

            expected_points

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (

            str(datetime.now()),

            market_data["nasdaq"]["percentage"],

            market_data["dow"]["percentage"],

            market_data["sp500"]["percentage"],

            market_data["nikkei"]["percentage"],

            market_data["hangseng"]["percentage"],

            market_data["crudeOil"]["percentage"],

            market_data["dxy"]["percentage"],

            market_data["vix"]["percentage"],

            nifty_data.get("current", 0),

            prediction["expectedMove"],

            prediction["expectedPoints"],
        )
    )

    conn.commit()

    conn.close()

# =====================================
# FETCH HISTORY
# =====================================

def fetch_history():

    conn = sqlite3.connect(
        "database/market_data.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM market_history
        ORDER BY id DESC
        LIMIT 100
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows
