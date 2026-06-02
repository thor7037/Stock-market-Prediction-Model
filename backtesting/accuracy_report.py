"""Accuracy and performance reporting."""


def generate_report(results: dict) -> dict:
    trades = results.get("trades", [])
    total = len(trades)
    wins = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
    pnl = sum(float(trade.get("pnl", 0)) for trade in trades)

    return {
        "total_trades": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": round((wins / total) * 100, 2) if total else 0.0,
        "total_pnl": round(pnl, 2),
    }
