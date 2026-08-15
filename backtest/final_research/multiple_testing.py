"""
Multiple Testing Module for NEXUS-7 Final Master Research
Calculates Deflated Sharpe Ratio (DSR), False Discovery Rate (FDR), and FWER corrections
to adjust for data-mining bias across all tested strategy candidates.
Pure Python/Numpy implementation with zero scipy dependency.
"""

from typing import Dict, List, Any
import math
import numpy as np


def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function (CDF)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Approximation of standard normal percent point function (quantile)."""
    if p <= 0.0:
        return -5.0
    if p >= 1.0:
        return 5.0
    # Beasley-Springer-Moro / Abramowitz & Stegun approximation
    t = math.sqrt(-2.0 * math.log(min(p, 1.0 - p)))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    val = t - ((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1.0)
    return -val if p < 0.5 else val


def calculate_deflated_sharpe_ratio_final(
    observed_sharpe: float,
    num_trials: int,
    var_sharpe: float = 1.0,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    sample_length: int = 100
) -> Dict[str, Any]:
    """
    Computes Deflated Sharpe Ratio (DSR) and p-value given the number of tested hypotheses.
    """
    if num_trials <= 1:
        num_trials = 1

    # Expected maximum Sharpe under null hypothesis
    euler_mascheroni = 0.5772156649
    p1 = max(1e-6, min(1.0 - 1e-6, 1.0 - 1.0 / num_trials))
    p2 = max(1e-6, min(1.0 - 1e-6, 1.0 - 1.0 / (num_trials * math.e)))

    exp_max_sharpe = math.sqrt(var_sharpe) * (
        (1.0 - euler_mascheroni) * _norm_ppf(p1) +
        euler_mascheroni * _norm_ppf(p2)
    )

    # Standard error of Sharpe ratio
    sr_std_err = math.sqrt(
        max(1e-8, (1.0 + (0.5 * observed_sharpe**2) - (skewness * observed_sharpe) + ((kurtosis - 3.0) / 4.0 * observed_sharpe**2)) / (sample_length - 1.0))
    )

    if sr_std_err <= 0:
        sr_std_err = 1.0 / math.sqrt(sample_length)

    dsr_statistic = (observed_sharpe - exp_max_sharpe) / sr_std_err
    p_value = 1.0 - _norm_cdf(dsr_statistic)

    is_significant = p_value < 0.05

    return {
        "observed_sharpe": round(float(observed_sharpe), 3),
        "num_trials_tested": num_trials,
        "expected_max_null_sharpe": round(float(exp_max_sharpe), 3),
        "dsr_statistic": round(float(dsr_statistic), 3),
        "p_value": round(float(p_value), 4),
        "is_statistically_significant": bool(is_significant)
    }
