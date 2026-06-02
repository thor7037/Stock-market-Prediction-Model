# =====================================
# STRIKE SELECTION ENGINE
# =====================================

import math


# =====================================
# ROUND TO STRIKE
# =====================================

def round_to_strike(price, step=50):
    return int(round(price / step) * step)


# =====================================
# MAIN STRATEGY ENGINE
# =====================================

def get_option_strategy(index, price, sentiment, move):

    if price == 0:
        return {"strategy": "No data"}

    atm = round_to_strike(price)

    # expected move in points
    move_points = (move / 100) * price

    upper = round_to_strike(price + abs(move_points))
    lower = round_to_strike(price - abs(move_points))

    # safety buffer (avoid too tight strikes)
    buffer = 100 if "NIFTY" in index.upper() else 200

    upper += buffer
    lower -= buffer

    # =====================================
    # SIDEWAYS → SELL PREMIUM
    # =====================================

    if sentiment == "Sideways":

        if abs(move) < 0.3:
            return {
                "strategy": "Iron Condor",
                "sell_pe": lower,
                "sell_ce": upper,
                "buy_pe": lower - 200,
                "buy_ce": upper + 200,
            }

        else:
            return {
                "strategy": "Short Strangle",
                "sell_pe": lower,
                "sell_ce": upper,
            }

    # =====================================
    # BULLISH
    # =====================================

    elif sentiment == "Bullish":

        if move > 0.7:
            return {
                "strategy": "Buy Call",
                "strike": atm,
            }

        else:
            return {
                "strategy": "Bull Call Spread",
                "buy_ce": atm,
                "sell_ce": atm + 200,
            }

    # =====================================
    # BEARISH
    # =====================================

    elif sentiment == "Bearish":

        if move < -0.7:
            return {
                "strategy": "Buy Put",
                "strike": atm,
            }

        else:
            return {
                "strategy": "Bear Put Spread",
                "buy_pe": atm,
                "sell_pe": atm - 200,
            }

    return {"strategy": "No clear trade"}