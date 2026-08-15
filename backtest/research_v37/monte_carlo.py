"""
Monte Carlo Simulation Module for NEXUS-7 Research V37
Executes 5,000-iteration 2D matrix vectorized trade-sequence shuffle simulations.
"""

from typing import Dict, List, Any
import numpy as np


def run_monte_carlo_simulations(
    pnls: List[float],
    initial_balance: float = 1000.0,
    iterations: int = 5000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs 5,000 vectorized Monte Carlo trade-sequence shuffles.
    """
    if not pnls or len(pnls) < 5:
        return {
            "median_drawdown_pct": 0.0,
            "p95_drawdown_pct": 0.0,
            "p99_drawdown_pct": 0.0,
            "prob_dd_gt_5pct": 0.0,
            "prob_dd_gt_10pct": 0.0,
            "prob_dd_gt_20pct": 0.0,
            "median_final_balance": initial_balance
        }

    np.random.seed(seed)
    pnls_arr = np.array(pnls, dtype=float)
    n_trades = len(pnls_arr)

    # 2D matrix trade shuffle
    shuffled_matrix = np.random.choice(pnls_arr, size=(iterations, n_trades), replace=True)
    equity_curves = initial_balance + np.cumsum(shuffled_matrix, axis=1)
    equity_curves = np.column_stack([np.full(iterations, initial_balance), equity_curves])

    peaks = np.maximum.accumulate(equity_curves, axis=1)
    drawdowns = (peaks - equity_curves) / peaks
    max_drawdowns = np.max(drawdowns, axis=1) * 100.0
    final_balances = equity_curves[:, -1]

    median_dd = float(np.median(max_drawdowns))
    p95_dd = float(np.percentile(max_drawdowns, 95))
    p99_dd = float(np.percentile(max_drawdowns, 99))

    prob_5 = float(np.mean(max_drawdowns > 5.0) * 100.0)
    prob_10 = float(np.mean(max_drawdowns > 10.0) * 100.0)
    prob_20 = float(np.mean(max_drawdowns > 20.0) * 100.0)

    return {
        "median_drawdown_pct": round(median_dd, 2),
        "p95_drawdown_pct": round(p95_dd, 2),
        "p99_drawdown_pct": round(p99_dd, 2),
        "prob_dd_gt_5pct": round(prob_5, 1),
        "prob_dd_gt_10pct": round(prob_10, 1),
        "prob_dd_gt_20pct": round(prob_20, 1),
        "median_final_balance": round(float(np.median(final_balances)), 2)
    }
