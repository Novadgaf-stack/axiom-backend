"""
Capital Simulation Module for NEXUS-7 Final Master Research
Simulates realistic account growth and risk of ruin across 5 capital tiers:
$100, $500, $1,000, $5,000, $10,000 account balances.
"""

from typing import Dict, List, Any
import numpy as np


def simulate_capital_growth_final(
    trades: List[Dict[str, Any]],
    capital_tiers: List[float] = None,
    risk_pct: float = 0.0050
) -> Dict[str, Dict[str, Any]]:
    """
    Simulates account growth and drawdown across initial capital levels.
    """
    if capital_tiers is None:
        capital_tiers = [100.0, 500.0, 1000.0, 5000.0, 10000.0]

    if not trades:
        return {f"${int(c)}": {"final_balance": c, "max_drawdown_pct": 0.0, "net_return_pct": 0.0} for c in capital_tiers}

    results = {}
    for cap in capital_tiers:
        balance = cap
        peak = balance
        max_dd = 0.0

        for t in trades:
            r_mult = t.get("r_multiple", 0.0)
            risk_amt = balance * risk_pct
            pnl = r_mult * risk_amt
            balance += pnl
            if balance > peak:
                peak = balance
            dd = (peak - balance) / (peak + 1e-8)
            if dd > max_dd:
                max_dd = dd

        results[f"${int(cap)}"] = {
            "initial_capital": cap,
            "final_balance": round(float(balance), 2),
            "net_return_pct": round(float((balance - cap) / cap * 100.0), 2),
            "max_drawdown_pct": round(float(max_dd * 100.0), 2),
            "trade_count": len(trades)
        }

    return results
