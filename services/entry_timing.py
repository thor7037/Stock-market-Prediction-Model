# =====================================
# ENTRY TIMING ENGINE
# =====================================

from datetime import datetime


# =====================================
# GET CURRENT TIME (IST)
# =====================================

def get_market_time():
    now = datetime.now()
    return now.hour, now.minute


# =====================================
# ENTRY DECISION LOGIC
# =====================================

def get_entry_plan(sentiment, move):

    hour, minute = get_market_time()
    current_minutes = hour * 60 + minute

    # Market timings (IST)
    market_open = 9 * 60 + 15        # 9:15
    safe_entry = 9 * 60 + 25         # 9:25
    late_entry = 11 * 60 + 30        # 11:30
    avoid_time = 14 * 60             # 2:00 PM

    # =====================================
    # BEFORE MARKET OPEN
    # =====================================

    if current_minutes < market_open:
        return {
            "action": "WAIT",
            "reason": "Market not open yet",
        }

    # =====================================
    # FIRST 10 MINUTES (HIGH VOLATILITY)
    # =====================================

    if current_minutes < safe_entry:
        return {
            "action": "WAIT",
            "reason": "Avoid first 10 min volatility",
        }

    # =====================================
    # SIDEWAYS MARKET
    # =====================================

    if sentiment == "Sideways":

        if current_minutes < late_entry:
            return {
                "action": "ENTER",
                "reason": "Good for range selling",
                "entryTime": "9:25 - 11:30",
            }

        else:
            return {
                "action": "AVOID",
                "reason": "Late entry risky for sideways",
            }

    # =====================================
    # TRENDING MARKET (BUY)
    # =====================================

    if sentiment in ["Bullish", "Bearish"]:

        if current_minutes < late_entry:
            return {
                "action": "ENTER",
                "reason": "Momentum window active",
                "entryTime": "9:25 - 11:30",
            }

        elif current_minutes < avoid_time:
            return {
                "action": "ENTER SMALL",
                "reason": "Late entry, reduce position size",
            }

        else:
            return {
                "action": "AVOID",
                "reason": "Too late, risk high",
            }

    # =====================================
    # DEFAULT
    # =====================================

    return {
        "action": "WAIT",
        "reason": "No clear setup",
    }