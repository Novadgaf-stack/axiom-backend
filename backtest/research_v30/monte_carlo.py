"""
NEXUS-7 Research V30 — Monte Carlo Simulation Module
Shuffles realized trade PnLs over 1,000 iterations to derive drawdown distributions,
losing streak distributions, and probability of drawdown thresholds (>10%, >20%).
"""

from typing import Dict, List, Any
import numpy as np


def run_monte_carlo_resampling(
    trades: List[Dict[str, Any]],
    initial_balance: float = 1000.0,
    iterations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Shuffles realized trade PnLs over 1,000 iterations while preserving the return distribution.
    Computes distribution statistics for returns, drawdowns, and losing streaks.
    """
    if not trades:
        return {
            "iterations": 0,
            "median_return": 0.0,
            "worst_case_return": 0.0,
            "best_case_return": 0.0,
            "dd_5th_percentile": 0.0,
            "dd_50th_percentile": 0.0,
            "dd_95th_percentile": 0.0,
            "prob_dd_over_10pct": 0.0,
            "prob_dd_over_20pct": 0.0,
            "prob_negative_return": 0.0,
            "max_losing_streak_95th": 0
        }

    pnls = np.array([t["net_pnl"] for t in trades])
    n = len(pnls)

    rng = np.random.default_rng(seed)

    final_balances = []
    max_dds = []
    losing_streaks = []

    for _ in range(iterations):
        shuffled_pnls = rng.choice(pnls, size=n, replace=False)

        # Equity curve
        eq = [initial_balance]
        b = initial_balance
        streak = 0
        max_strk = 0

        for p in shuffled_pnls:
            b += p
            eq.append(b)

            if p < 0:
                streak += 1
                max_strk = max(max_strk, streak)
            else:
                streak = 0

        final_balances.append(b)
        losing_streaks.append(max_strk)

        eq_arr = np.array(eq)
        peak = np.maximum.accumulate(eq_arr)
        dd = (peak - eq_arr) / peak
        max_dds.append(float(np.max(dd)))

    final_balances = np.array(final_balances)
    max_dds = np.array(max_dds)
    losing_streaks = np.array(losing_streaks)

    returns_pct = (final_balances - initial_balance) / initial_balance

    prob_dd_10 = float(np.mean(max_dds > 0.10) * 100.0)
    prob_dd_20 = float(np.mean(max_dds > 0.20) * 100.0)
    prob_neg_ret = float(np.mean(returns_pct < 0) * 100.0)

    return {
        "iterations": iterations,
        "median_return_pct": round(float(np.median(returns_pct) * 100), 2),
        "worst_case_return_pct": round(float(np.min(returns_pct) * 100), 2),
        "best_case_return_pct": round(float(np.max(returns_pct) * 100), 2),
        "dd_5th_percentile": round(float(np.percentile(max_dds, 5) * 100), 2),
        "dd_50th_percentile": round(float(np.percentile(max_dds, 50) * 100), 2),
        "dd_95th_percentile": round(float(np.percentile(max_dds, 95) * 100), 2),
        "prob_dd_over_10pct": round(prob_dd_10, 1),
        "prob_dd_over_20pct": round(prob_dd_20, 1),
        "prob_negative_return": round(prob_neg_ret, 1),
        "max_losing_streak_95th": int(np.percentile(losing_streaks, 95))
    }
