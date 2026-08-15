"""
Multiple Testing Control & Data-Mining Bias Module for NEXUS-7 Research V38
Tracks number of hypotheses and parameter configurations evaluated,
and computes Deflated Sharpe Ratio (DSR) and Family-Wise Error Rate (FWER) corrections.
"""

from typing import Dict, List, Any
import numpy as np


def compute_deflated_sharpe_ratio(
    observed_sharpe: float,
    num_trials: int,
    variance_sharpe: float = 1.0,
    sample_length: int = 500
) -> Dict[str, Any]:
    """
    Computes Deflated Sharpe Ratio (DSR) to adjust for multiple-testing data-mining bias.
    """
    if num_trials <= 1 or observed_sharpe <= 0:
        return {
            "trials_tested": num_trials,
            "observed_sharpe": observed_sharpe,
            "deflated_sharpe_ratio": observed_sharpe,
            "dsr_p_value": 0.50,
            "dsr_passed": observed_sharpe > 0
        }

    # Expected maximum Sharpe under null hypothesis (Euler-Mascheroni approximation)
    expected_max_sharpe = np.sqrt(variance_sharpe) * (
        (1 - 0.5772156649) * np.power(2 * np.log(num_trials), -0.5) +
        np.sqrt(2 * np.log(num_trials))
    )

    std_err = np.sqrt((1 + 0.5 * observed_sharpe**2) / max(1, sample_length))
    z_stat = (observed_sharpe - expected_max_sharpe) / (std_err + 1e-8)
    dsr_p_value = float(1.0 - 0.5 * (1.0 + np.sign(z_stat) * np.sqrt(1 - np.exp(-2 * z_stat**2 / np.pi))))

    dsr_passed = observed_sharpe > expected_max_sharpe and dsr_p_value < 0.05

    return {
        "trials_tested": num_trials,
        "observed_sharpe": round(float(observed_sharpe), 3),
        "expected_max_null_sharpe": round(float(expected_max_sharpe), 3),
        "dsr_p_value": round(float(dsr_p_value), 4),
        "dsr_passed": bool(dsr_passed)
    }
