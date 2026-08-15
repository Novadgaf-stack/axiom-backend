"""
Position Sizing Module for NEXUS-7 Research V38
Implements Stop-Distance Position Sizing models across 0.25%, 0.50%, 0.75%, 1.00% risk budgets.
"""

from typing import Dict, List, Any
import numpy as np


def compute_stop_distance_position_size_v38(
    equity: float,
    entry_price: float,
    stop_price: float,
    risk_budget_pct: float = 0.0050, # 0.50% research default
    max_position_equity_pct: float = 0.20
) -> Dict[str, float]:
    """
    Stop-distance position sizing formula:
    Units = (Equity * Risk_Pct) / Stop_Distance
    """
    stop_distance = abs(entry_price - stop_price)
    if stop_distance <= 1e-6 or entry_price <= 0 or equity <= 0:
        return {"units": 0.0, "position_usd": 0.0, "risk_usd": 0.0}

    risk_usd = equity * risk_budget_pct
    units = risk_usd / stop_distance

    max_notional_usd = equity * max_position_equity_pct
    max_units = max_notional_usd / entry_price
    units = min(units, max_units)

    position_usd = units * entry_price

    return {
        "units": round(float(units), 6),
        "position_usd": round(float(position_usd), 2),
        "risk_usd": round(float(risk_usd), 2),
        "risk_pct": risk_budget_pct
    }
