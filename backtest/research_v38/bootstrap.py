"""
Bootstrap Resampling Module for NEXUS-7 Research V38
Executes 10,000-iteration Bootstrap resampling strictly on OOS trades for 95% Confidence Intervals.
"""

from typing import Dict, List, Any
import numpy as np


def run_bootstrap_resampling_v38(
    pnls: List[float],
    iterations: int = 10000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs 10,000 Bootstrap iterations to compute 95% CIs for Profit Factor and Expectancy.
    """
    if not pnls or len(pnls) < 5:
        return {
            "pf_ci": [0.0, 0.0],
            "exp_ci": [0.0, 0.0],
            "win_rate_ci": [0.0, 0.0],
            "bootstrap_passed": False
        }

    np.random.seed(seed)
    pnls_arr = np.array(pnls, dtype=float)
    n = len(pnls_arr)

    # 2D matrix vectorized resampling
    samples = np.random.choice(pnls_arr, size=(iterations, n), replace=True)

    wins = np.where(samples > 0, samples, 0.0)
    losses = np.where(samples < 0, np.abs(samples), 0.0)

    sum_wins = np.sum(wins, axis=1)
    sum_losses = np.sum(losses, axis=1)

    pfs = np.where(sum_losses > 0, sum_wins / sum_losses, np.where(sum_wins > 0, 99.0, 0.0))
    expectancies = np.mean(samples, axis=1)
    win_rates = np.mean(samples > 0, axis=1) * 100.0

    alpha = (1.0 - confidence_level) / 2.0
    lower_idx = int(iterations * alpha)
    upper_idx = int(iterations * (1.0 - alpha))

    pfs_sorted = np.sort(pfs)
    exp_sorted = np.sort(expectancies)
    wr_sorted = np.sort(win_rates)

    pf_ci = [round(float(pfs_sorted[lower_idx]), 3), round(float(pfs_sorted[upper_idx]), 3)]
    exp_ci = [round(float(exp_sorted[lower_idx]), 2), round(float(exp_sorted[upper_idx]), 2)]
    wr_ci = [round(float(wr_sorted[lower_idx]), 1), round(float(wr_sorted[upper_idx]), 1)]

    bootstrap_passed = pf_ci[0] > 1.00 and exp_ci[0] > 0.0

    return {
        "pf_ci": pf_ci,
        "exp_ci": exp_ci,
        "win_rate_ci": wr_ci,
        "bootstrap_passed": bootstrap_passed
    }
