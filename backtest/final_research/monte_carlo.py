"""
Monte Carlo Simulation Module for NEXUS-7 Final Master Research
10,000-iteration 2D matrix trade sequence shuffles & risk of ruin simulation.
Computes 95% worst-case max drawdown and risk of ruin probability.
"""

from typing import Dict, List, Any
import numpy as np


def run_monte_carlo_simulation_final(
    trades: List[Dict[str, Any]],
    num_simulations: int = 10000,
    initial_equity: float = 10000.0,
    ruin_threshold_pct: float = 0.50
) -> Dict[str, Any]:
    """
    Executes 10,000 Monte Carlo trade sequence shuffles.
    """
    if not trades:
        return {
            "median_drawdown_pct": 0.0,
            "max_drawdown_95_pct": 0.0,
            "max_drawdown_99_pct": 0.0,
            "risk_of_ruin_pct": 0.0,
            "median_final_equity": initial_equity
        }

    pnls = np.array([t["net_pnl"] for t in trades], dtype=np.float64)
    n = len(pnls)
    if n == 0:
        return {
            "median_drawdown_pct": 0.0,
            "max_drawdown_95_pct": 0.0,
            "max_drawdown_99_pct": 0.0,
            "risk_of_ruin_pct": 0.0,
            "median_final_equity": initial_equity
        }

    # Vectorized 2D matrix trade shuffling
    shuffled_indices = np.random.rand(num_simulations, n).argsort(axis=1)
    shuffled_pnls = pnls[shuffled_indices]

    equity_curves = initial_equity + np.cumsum(shuffled_pnls, axis=1)
    running_max = np.maximum.accumulate(equity_curves, axis=1)
    drawdowns = (running_max - equity_curves) / (running_max + 1e-8)
    max_dds = np.max(drawdowns, axis=1)

    final_equities = equity_curves[:, -1]
    ruin_level = initial_equity * (1.0 - ruin_threshold_pct)
    ruined_count = np.sum(np.min(equity_curves, axis=1) <= ruin_level)

    return {
        "median_drawdown_pct": round(float(np.median(max_dds) * 100.0), 2),
        "max_drawdown_95_pct": round(float(np.percentile(max_dds, 95) * 100.0), 2),
        "max_drawdown_99_pct": round(float(np.percentile(max_dds, 99) * 100.0), 2),
        "risk_of_ruin_pct": round(float(ruined_count / num_simulations * 100.0), 2),
        "median_final_equity": round(float(np.median(final_equities)), 2)
    }
