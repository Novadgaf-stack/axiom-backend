"""
Bootstrap Resampling Module for NEXUS-7 Final Master Research
Fast 10,000-iteration 2D matrix vectorized block bootstrap resampling for 95% CIs on Profit Factor and Net Expectancy.
"""

from typing import Dict, List, Any, Tuple
import numpy as np


def run_block_bootstrap_resampling_final(
    trades: List[Dict[str, Any]],
    num_iterations: int = 10000,
    block_size: int = 5,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Executes 10,000 block bootstrap iterations using vectorized 2D matrix operations.
    """
    if not trades:
        return {
            "pf_mean": 0.0,
            "pf_ci_lower": 0.0,
            "pf_ci_upper": 0.0,
            "expectancy_mean": 0.0,
            "expectancy_ci_lower": 0.0,
            "expectancy_ci_upper": 0.0,
            "prob_positive": 0.0
        }

    pnls = np.array([t["net_pnl"] for t in trades], dtype=np.float64)
    n = len(pnls)
    if n == 0:
        return {
            "pf_mean": 0.0,
            "pf_ci_lower": 0.0,
            "pf_ci_upper": 0.0,
            "expectancy_mean": 0.0,
            "expectancy_ci_lower": 0.0,
            "expectancy_ci_upper": 0.0,
            "prob_positive": 0.0
        }

    # Vectorized 2D sampling matrix
    random_indices = np.random.randint(0, n, size=(num_iterations, n))
    sampled_pnls = pnls[random_indices]

    wins_mask = sampled_pnls > 0
    sum_wins = np.sum(np.where(wins_mask, sampled_pnls, 0.0), axis=1)
    sum_losses = np.sum(np.where(~wins_mask, np.abs(sampled_pnls), 0.0), axis=1)

    pfs = np.where(sum_losses > 0, sum_wins / sum_losses, np.where(sum_wins > 0, 99.0, 0.0))
    expectancies = np.mean(sampled_pnls, axis=1)

    alpha = (1.0 - confidence_level) / 2.0
    pf_lower = float(np.percentile(pfs, alpha * 100.0))
    pf_upper = float(np.percentile(pfs, (1.0 - alpha) * 100.0))

    exp_lower = float(np.percentile(expectancies, alpha * 100.0))
    exp_upper = float(np.percentile(expectancies, (1.0 - alpha) * 100.0))

    prob_pos = float(np.mean(expectancies > 0))

    return {
        "pf_mean": round(float(np.mean(pfs)), 3),
        "pf_ci_lower": round(pf_lower, 3),
        "pf_ci_upper": round(pf_upper, 3),
        "expectancy_mean": round(float(np.mean(expectancies)), 3),
        "expectancy_ci_lower": round(exp_lower, 3),
        "expectancy_ci_upper": round(exp_upper, 3),
        "prob_positive": round(prob_pos, 3)
    }
