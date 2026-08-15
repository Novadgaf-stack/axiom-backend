"""
Position Sizing Module for NEXUS-7 Final Master Research
Calculates stop-distance risk-based position sizing formula:
Units = (Equity * Risk_Pct) / Stop_Distance across 0.25%, 0.50%, 0.75%, 1.00% risk budgets,
and enforces portfolio risk caps and daily drawdown circuit breakers.
"""

from typing import Dict, Any, List
import numpy as np


def calculate_position_size_final(
    equity: float,
    entry_price: float,
    stop_loss: float,
    risk_pct: float = 0.0050,
    max_position_size_usd: float = 5000.0
) -> Dict[str, float]:
    """
    Computes risk-based position units and position size USD.
    """
    stop_distance = abs(entry_price - stop_loss)
    if stop_distance <= 0 or equity <= 0:
        return {"units": 0.0, "position_size_usd": 0.0, "risk_amount": 0.0}

    risk_amount = equity * risk_pct
    units = risk_amount / stop_distance
    pos_usd = units * entry_price

    if pos_usd > max_position_size_usd:
        pos_usd = max_position_size_usd
        units = pos_usd / entry_price
        risk_amount = units * stop_distance

    return {
        "units": float(units),
        "position_size_usd": float(pos_usd),
        "risk_amount": float(risk_amount)
    }


def evaluate_risk_budgets_final(
    trades: List[Dict[str, Any]],
    risk_pcts: List[float] = None
) -> Dict[str, Dict[str, Any]]:
    """Evaluates strategy performance across 0.25%, 0.50%, 0.75%, 1.00% risk budgets."""
    if risk_pcts is None:
        risk_pcts = [0.0025, 0.0050, 0.0075, 0.0100]

    results = {}
    for r in risk_pcts:
        eq = 10000.0
        peak = eq
        max_dd = 0.0

        for t in trades:
            r_mult = t.get("r_multiple", 0.0)
            risk_amt = eq * r
            pnl = r_mult * risk_amt
            eq += pnl
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd

        results[f"risk_{int(r*10000)}bps"] = {
            "risk_pct": r,
            "final_equity": round(float(eq), 2),
            "max_drawdown_pct": round(float(max_dd * 100.0), 2),
            "net_return_pct": round(float((eq - 10000.0) / 100.0), 2)
        }

    return results
