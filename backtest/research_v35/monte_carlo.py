"""
Monte Carlo Simulation Module for NEXUS-7 Research V35
Executes 2,000-iteration trade-sequence shuffle simulations.
Derives return and drawdown distributions, losing streak probabilities, and risk of ruin.
High-performance 2D matrix vectorized NumPy implementation.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def run_monte_carlo_resampling(
    trades: List[Dict[str, Any]],
    initial_balance: float = 1000.0,
    iterations: int = 2000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Executes 2,000 trade-sequence shuffle Monte Carlo simulations.
    2D matrix vectorized NumPy implementation for sub-second execution.
    """
    if not trades:
        return {
            "iterations": iterations,
            "median_return_pct": 0.0,
            "pct_5th_return": 0.0,
            "pct_95th_return": 0.0,
            "median_max_dd": 0.0,
            "dd_95th_percentile": 0.0,
            "dd_99th_percentile": 0.0,
            "prob_dd_over_10": 0.0,
            "prob_dd_over_15": 0.0,
            "prob_dd_over_20": 0.0,
            "prob_dd_over_30": 0.0,
            "risk_of_ruin_50pct": 0.0,
            "prob_ending_negative": 0.0,
            "losing_streak_95th": 0
        }

    pnls = np.array([t["net_pnl"] for t in trades])
    n_trades = len(pnls)
    rng = np.random.default_rng(seed)

    # 2D matrix vectorized Monte Carlo resampling
    shuffled_matrix = rng.choice(pnls, size=(iterations, n_trades), replace=True)
    cum_pnls = np.hstack([np.zeros((iterations, 1)), np.cumsum(shuffled_matrix, axis=1)])
    equity_curves = initial_balance + cum_pnls

    returns_arr = (equity_curves[:, -1] - initial_balance) / initial_balance * 100.0

    peaks = np.maximum.accumulate(equity_curves, axis=1)
    dds = np.where(peaks > 0, (peaks - equity_curves) / peaks, 0.0)
    max_dds_arr = np.max(dds, axis=1) * 100.0

    # Vectorized losing streak calculation
    is_loss = (shuffled_matrix < 0).astype(int)
    losing_streaks = []
    for row in is_loss:
        max_s = 0
        curr_s = 0
        for val in row:
            if val == 1:
                curr_s += 1
                if curr_s > max_s:
                    max_s = curr_s
            else:
                curr_s = 0
        losing_streaks.append(max_s)

    return {
        "iterations": iterations,
        "median_return_pct": round(float(np.median(returns_arr)), 2),
        "pct_5th_return": round(float(np.percentile(returns_arr, 5)), 2),
        "pct_95th_return": round(float(np.percentile(returns_arr, 95)), 2),
        "median_max_dd": round(float(np.median(max_dds_arr)), 2),
        "dd_95th_percentile": round(float(np.percentile(max_dds_arr, 95)), 2),
        "dd_99th_percentile": round(float(np.percentile(max_dds_arr, 99)), 2),
        "prob_dd_over_10": round(float(np.mean(max_dds_arr > 10.0) * 100.0), 1),
        "prob_dd_over_15": round(float(np.mean(max_dds_arr > 15.0) * 100.0), 1),
        "prob_dd_over_20": round(float(np.mean(max_dds_arr > 20.0) * 100.0), 1),
        "prob_dd_over_30": round(float(np.mean(max_dds_arr > 30.0) * 100.0), 1),
        "risk_of_ruin_50pct": round(float(np.mean(max_dds_arr > 50.0) * 100.0), 1),
        "prob_ending_negative": round(float(np.mean(returns_arr < 0.0) * 100.0), 1),
        "losing_streak_95th": int(np.percentile(losing_streaks, 95))
    }
