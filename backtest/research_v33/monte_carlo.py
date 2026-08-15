"""
Monte Carlo Simulation Module for NEXUS-7 Research V33
Executes 2,000-iteration trade-sequence shuffle simulations.
Derives return and drawdown distributions, losing streak probabilities, and risk of ruin.
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
    Calculates median, 5th, and 95th percentile drawdowns and returns.
    """
    if not trades:
        return {
            "iterations": iterations,
            "median_return_pct": 0.0,
            "pct_5th_return": 0.0,
            "pct_95th_return": 0.0,
            "median_max_dd": 0.0,
            "dd_95th_percentile": 0.0,
            "prob_dd_over_10": 0.0,
            "prob_dd_over_20": 0.0,
            "prob_dd_over_30": 0.0,
            "risk_of_ruin_50pct": 0.0,
            "prob_ending_negative": 0.0,
            "losing_streak_95th": 0
        }

    pnls = np.array([t["net_pnl"] for t in trades])
    n_trades = len(pnls)

    rng = np.random.default_rng(seed)

    final_returns = []
    max_dds = []
    losing_streaks = []

    for _ in range(iterations):
        shuffled_pnls = rng.choice(pnls, size=n_trades, replace=True)
        equity_curve = initial_balance + np.insert(np.cumsum(shuffled_pnls), 0, 0.0)

        tot_ret = (equity_curve[-1] - initial_balance) / initial_balance * 100.0
        final_returns.append(tot_ret)

        peaks = np.maximum.accumulate(equity_curve)
        dds = np.where(peaks > 0, (peaks - equity_curve) / peaks, 0.0)
        max_dd = float(np.max(dds))
        max_dds.append(max_dd * 100.0)


        # Measure longest losing streak
        max_streak = 0
        curr_streak = 0
        for p in shuffled_pnls:
            if p < 0:
                curr_streak += 1
                if curr_streak > max_streak:
                    max_streak = curr_streak
            else:
                curr_streak = 0
        losing_streaks.append(max_streak)

    max_dds_arr = np.array(max_dds)
    returns_arr = np.array(final_returns)

    return {
        "iterations": iterations,
        "median_return_pct": round(float(np.median(returns_arr)), 2),
        "pct_5th_return": round(float(np.percentile(returns_arr, 5)), 2),
        "pct_95th_return": round(float(np.percentile(returns_arr, 95)), 2),
        "median_max_dd": round(float(np.median(max_dds_arr)), 2),
        "dd_95th_percentile": round(float(np.percentile(max_dds_arr, 95)), 2),
        "prob_dd_over_10": round(float(np.mean(max_dds_arr > 10.0) * 100.0), 1),
        "prob_dd_over_20": round(float(np.mean(max_dds_arr > 20.0) * 100.0), 1),
        "prob_dd_over_30": round(float(np.mean(max_dds_arr > 30.0) * 100.0), 1),
        "risk_of_ruin_50pct": round(float(np.mean(max_dds_arr > 50.0) * 100.0), 1),
        "prob_ending_negative": round(float(np.mean(returns_arr < 0.0) * 100.0), 1),
        "losing_streak_95th": int(np.percentile(losing_streaks, 95))
    }
