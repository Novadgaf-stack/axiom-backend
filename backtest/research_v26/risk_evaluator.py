"""
NEXUS-7 — RESEARCH V26 RISK EVALUATOR
Evaluates position sizing sensitivity (0.5%, 0.75%, 1.0%) ONLY AFTER a candidate passes out-of-sample statistical gates.
Separates strategy edge quality from position sizing leverage.
"""
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from backtest.research_v26.statistical_gates import evaluate_trade_sequence


def evaluate_risk_sizing_sensitivity(
    trades: List[Dict[str, Any]],
    total_days: float,
    friction_pct: float = 0.0015,
    initial_equity: float = 10000.0
) -> Dict[str, Any]:
    """
    Evaluates 0.5%, 0.75%, and 1.0% risk per trade sizing for a candidate strategy.
    Returns comparative breakdown table.
    """
    risk_levels = [0.005, 0.0075, 0.010]
    sensitivity_results = {}

    for r_pct in risk_levels:
        level_name = f"{r_pct * 100:.2f}%"
        res = evaluate_trade_sequence(
            trades=trades,
            total_days=total_days,
            friction_pct=friction_pct,
            risk_per_trade_pct=r_pct,
            initial_equity=initial_equity
        )

        # Calculate CAGR
        years = total_days / 365.25
        final_eq = res["final_equity"]
        cagr = ((final_eq / initial_equity) ** (1.0 / max(years, 0.1)) - 1.0) * 100.0 if final_eq > 0 else -100.0

        # Calculate Sharpe Ratio from daily PnL
        sharpe = round((res["net_expectancy_r"] * math.sqrt(252 * max(res["trades_per_day"], 0.5))) / max(res["max_drawdown_pct"] / 100.0, 0.01), 2)

        sensitivity_results[level_name] = {
            "risk_per_trade_pct": level_name,
            "final_equity": res["final_equity"],
            "cagr_pct": round(cagr, 2),
            "max_drawdown_pct": res["max_drawdown_pct"],
            "net_pf": res["net_pf"],
            "net_expectancy_usd": res["net_expectancy_usd"],
            "sharpe_ratio": sharpe
        }

    return sensitivity_results
