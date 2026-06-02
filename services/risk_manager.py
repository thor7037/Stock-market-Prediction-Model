# =====================================
# RISK MANAGEMENT ENGINE
# =====================================

def get_risk_plan(strategy, capital=100000):

    risk_per_trade = 0.02  # 2% risk
    max_risk = capital * risk_per_trade

    plan = {
        "capital": capital,
        "riskAmount": round(max_risk, 2),
    }

    strat = strategy.get("strategy", "")

    # =====================================
    # SELL STRATEGIES (CONDOR / STRANGLE)
    # =====================================

    if strat in ["Iron Condor", "Short Strangle"]:

        plan.update({
            "type": "SELL",
            "stopLoss": "25-30%",
            "target": "40-60%",
            "note": "Exit if one side breaks",
            "lotSize": 1 if max_risk < 3000 else 2,
        })

    # =====================================
    # BUY STRATEGIES
    # =====================================

    elif strat in ["Buy Call", "Buy Put"]:

        plan.update({
            "type": "BUY",
            "stopLoss": "40%",
            "target": "80-120%",
            "note": "Momentum trade",
            "lotSize": 1,
        })

    # =====================================
    # SPREAD STRATEGIES
    # =====================================

    elif strat in ["Bull Call Spread", "Bear Put Spread"]:

        plan.update({
            "type": "SPREAD",
            "stopLoss": "30%",
            "target": "50-70%",
            "note": "Defined risk strategy",
            "lotSize": 1,
        })

    else:
        plan.update({
            "type": "NO TRADE",
            "note": "No clear edge",
            "lotSize": 0,
        })

    return plan