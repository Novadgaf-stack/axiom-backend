"""
Combinatorial Purged Cross-Validation (CSCV) and Probability of Backtest Overfitting (PBO) Module.
Quantifies the probability that historical in-sample optimization resulted in a false discovery.
"""
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


def compute_pbo_cscv(strategy_returns_matrix: np.ndarray, num_splits: int = 10) -> Dict[str, float]:
    """
    Computes Probability of Backtest Overfitting (PBO) using CSCV partitioning across candidate strategies.
    
    Parameters:
    - strategy_returns_matrix: 2D array of shape (num_bars, num_strategies) containing return series.
    - num_splits: Number of equal time blocks N for CSCV combination.

    Returns:
    - Dict containing:
      - pbo_pct: Probability of Backtest Overfitting %
      - mean_oos_sharpe: Mean Sharpe ratio of in-sample selected strategies when tested OOS
      - prob_oos_sharpe_gt_0: Probability that OOS Sharpe ratio is > 0
    """
    num_bars, num_strats = strategy_returns_matrix.shape
    if num_strats < 2 or num_bars < 100:
        # Single strategy or insufficient sample fallback
        return {
            "pbo_pct": 50.0,
            "mean_oos_sharpe": 0.0,
            "prob_oos_sharpe_gt_0": 50.0,
            "deflated_sharpe_ratio": 0.0,
        }

    block_size = num_bars // num_splits
    blocks = [strategy_returns_matrix[i * block_size : (i + 1) * block_size] for i in range(num_splits)]

    # Generate combinations (C(N, N/2))
    from itertools import combinations
    half_split = num_splits // 2
    combos = list(combinations(range(num_splits), half_split))

    is_best_oos_logits = []
    oos_sharpes = []

    for is_indices in combos:
        oos_indices = [i for i in range(num_splits) if i not in is_indices]

        is_data = np.vstack([blocks[i] for i in is_indices])
        oos_data = np.vstack([blocks[i] for i in oos_indices])

        # Compute In-Sample Sharpe ratios
        is_means = np.mean(is_data, axis=0)
        is_stds = np.std(is_data, axis=0) + 1e-9
        is_sharpes = (is_means / is_stds) * np.sqrt(8760)

        # Select best In-Sample strategy
        best_is_idx = np.argmax(is_sharpes)

        # Evaluate selected strategy on Out-of-Sample data
        oos_means = np.mean(oos_data, axis=0)
        oos_stds = np.std(oos_data, axis=0) + 1e-9
        oos_sharpes_all = (oos_means / oos_stds) * np.sqrt(8760)

        selected_oos_sharpe = oos_sharpes_all[best_is_idx]
        oos_sharpes.append(selected_oos_sharpe)

        # Logit relative rank in OOS
        oos_rank = np.sum(oos_sharpes_all < selected_oos_sharpe) / (num_strats - 1 + 1e-9)
        # Overfitted if selected strategy ranks below median (rank < 0.5) in OOS
        is_best_oos_logits.append(1 if oos_rank < 0.5 else 0)

    pbo_pct = float(np.mean(is_best_oos_logits) * 100.0)
    mean_oos_sharpe = float(np.mean(oos_sharpes))
    prob_oos_sharpe_gt_0 = float(np.mean(np.array(oos_sharpes) > 0) * 100.0)

    return {
        "pbo_pct": round(pbo_pct, 2),
        "mean_oos_sharpe": round(mean_oos_sharpe, 3),
        "prob_oos_sharpe_gt_0": round(prob_oos_sharpe_gt_0, 2),
        "deflated_sharpe_ratio": round(mean_oos_sharpe * (1.0 - pbo_pct / 100.0), 3),
    }
