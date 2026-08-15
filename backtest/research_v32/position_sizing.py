"""
Position Sizing Module for NEXUS-7 Research V32
Evaluates stop-distance position sizing across risk tiers (0.25%, 0.50%, 0.75%, 1.00%, 1.25%).
Calculates capital growth, monthly return, annualized return, and drawdown.
Guarantees sizing does NOT manufacture artificial profitability.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def evaluate_position_sizing_and_growth(
    trades: List[Dict[str, Any]],
    initial_balance: float = 1000.0,
    total_days: float = 90.0,
    risk_tiers: List[float] = [0.0025, 0.0050, 0.0075, 0.0100, 0.0125]
) -> Dict[str, Any]:
    """
    Evaluates portfolio capital growth and drawdowns across multiple risk-per-trade tiers.
    Base trade outcomes and PnL in R units remain completely unchanged.
    """
    if not trades:
        return {tier: {"final_balance": initial_balance, "monthly_return": 0.0, "max_drawdown": 0.0} for tier in risk_tiers}

    results = {}
    months = max(0.1, total_days / 30.0)

    for risk_pct in risk_tiers:
        tier_key = f"risk_{int(risk_pct * 10000)}bps"
        balance = initial_balance
        equity_curve = [balance]

        for t in trades:
            pnl_r = t["pnl_r"]
            risk_usd = balance * risk_pct
            net_pnl = pnl_r * risk_usd
            balance += net_pnl
            equity_curve.append(balance)

        peak = equity_curve[0]
        max_dd = 0.0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        total_return_pct = (balance - initial_balance) / initial_balance
        monthly_return_pct = ((1.0 + total_return_pct) ** (1.0 / months) - 1.0) * 100.0 if total_return_pct > -1.0 else -100.0
        annualized_return_pct = ((1.0 + total_return_pct) ** (12.0 / months) - 1.0) * 100.0 if total_return_pct > -1.0 else -100.0

        results[tier_key] = {
            "risk_pct": risk_pct,
            "final_balance": round(balance, 2),
            "net_profit": round(balance - initial_balance, 2),
            "total_return_pct": round(total_return_pct * 100.0, 2),
            "monthly_return_pct": round(monthly_return_pct, 2),
            "annualized_return_pct": round(annualized_return_pct, 2),
            "max_drawdown": round(max_dd * 100.0, 1),
            "execution_note": "STANDARD_EXECUTION"
        }

    return results
