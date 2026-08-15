"""
Multiple Testing & Selection Bias Adjustment Module for NEXUS-7 Research V34
Calculates deflated performance metrics and tracks candidate/universe evaluation counts
to ensure reported robustness accounts for data snooping / selection bias.
"""

from typing import Dict, List, Any
import numpy as np


def compute_multiple_testing_correction(
    total_candidates_tested: int,
    total_universes_tested: int,
    total_parameter_sets_tested: int,
    top_sharpe: float = 0.0
) -> Dict[str, Any]:
    """
    Computes multiple-testing correction factor and deflated Sharpe ratio estimate.
    Adjustment Factor = sqrt(2 * ln(total_trials))
    Deflated Sharpe = max(0, top_sharpe - Adjustment Factor * 0.25)
    """
    total_trials = max(1, total_candidates_tested * total_universes_tested * total_parameter_sets_tested)
    adjustment_factor = float(np.sqrt(2.0 * np.log(max(2, total_trials))))
    deflated_sharpe = max(0.0, float(top_sharpe - adjustment_factor * 0.25))

    is_significant = bool(deflated_sharpe > 0.50)

    return {
        "total_candidates_tested": total_candidates_tested,
        "total_universes_tested": total_universes_tested,
        "total_parameter_sets_tested": total_parameter_sets_tested,
        "total_trials": total_trials,
        "adjustment_factor": round(adjustment_factor, 3),
        "raw_top_sharpe": round(top_sharpe, 2),
        "deflated_sharpe": round(deflated_sharpe, 2),
        "is_statistically_significant": is_significant
    }
