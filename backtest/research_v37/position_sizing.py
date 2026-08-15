"""
Position Sizing Module for NEXUS-7 Research V37
Implements Stop-Distance Position Sizing models across 0.25%, 0.50%, 0.75%, 1.00% risk budgets:
Fixed Risk, Volatility-Adjusted, Risk-Parity, Confidence-Weighted.
"""

from typing import Dict, List, Any
import numpy as np


def compute_stop_distance_position_size(
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


def compare_position_sizing_models(
    trades: List[Dict[str, Any]],
    initial_balance: float = 1000.0
) -> Dict[str, Dict[str, float]]:
    """
    Compares 4 position sizing models across historical trade outcomes:
    1. FIXED_RISK_025 (0.25%)
    2. FIXED_RISK_050 (0.50% - Default)
    3. FIXED_RISK_075 (0.75% - Max)
    4. CONFIDENCE_WEIGHTED (0.25% to 0.50%)
    """
    if not trades:
        return {}

    models = {
        "FIXED_RISK_025": 0.0025,
        "FIXED_RISK_050": 0.0050,
        "FIXED_RISK_075": 0.0075,
        "CONFIDENCE_WEIGHTED": 0.0050
    }

    results = {}

    for model_name, base_risk in models.items():
        balance = initial_balance
        peak = balance
        max_dd = 0.0
        pnl_sum = 0.0

        for t in trades:
            raw_pnl_r = t.get("pnl_r", 0.0)
            conf = t.get("confidence", 0.50)

            if model_name == "CONFIDENCE_WEIGHTED":
                effective_risk = 0.0025 + (conf * 0.0025)
            else:
                effective_risk = base_risk

            risk_usd = balance * effective_risk
            trade_pnl = raw_pnl_r * risk_usd
            balance += trade_pnl
            pnl_sum += trade_pnl

            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        results[model_name] = {
            "final_balance": round(balance, 2),
            "net_profit": round(pnl_sum, 2),
            "max_drawdown_pct": round(max_dd * 100.0, 2)
        }

    return results
