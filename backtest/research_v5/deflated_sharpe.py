"""
NEXUS-7 — DEFLATED SHARPE RATIO & MULTIPLE-TESTING AUDITOR (RESEARCH V5)
Adjusts Sharpe Ratio for backtest trial count and non-normal return distributions (Bailey & López de Prado, 2014).
Zero external dependencies (uses standard Python math library).
"""
import math
from typing import Dict


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """Approximation of the inverse standard normal Cumulative Distribution Function."""
    p = max(1e-9, min(1.0 - 1e-9, p))
    # Abramowitz and Stegun formula 26.2.23
    if p < 0.5:
        t = math.sqrt(-2.0 * math.log(p))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        return -((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1.0)
    else:
        t = math.sqrt(-2.0 * math.log(1.0 - p))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        return ((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1.0)


class DeflatedSharpeAuditor:
    """Calculates Deflated Sharpe Ratio (DSR) to prevent multiple-testing overfitting."""

    @staticmethod
    def calculate_dsr(
        observed_sharpe: float,
        num_trials: int = 50,
        variance_sharpe: float = 0.25,
        skewness: float = 0.0,
        kurtosis: float = 3.0,
        sample_length: int = 250
    ) -> Dict:
        """
        Calculates DSR probability. Returns Dict with dsr_prob, target_sharpe, and verdict.
        """
        if observed_sharpe <= 0 or sample_length < 2:
            return {
                "observed_sharpe": observed_sharpe,
                "dsr_prob": 0.0,
                "target_sharpe_threshold": 0.0,
                "verdict": "REJECTED (Sharpe <= 0)",
            }

        # Expected maximum Sharpe under NULL hypothesis of 0 true Sharpe across N trials
        # Euler-Mascheroni approximation for max of N standard normal variables
        p1 = 1.0 - 1.0 / num_trials
        p2 = 1.0 - 1.0 / (num_trials * math.e)
        e_max_sharpe = math.sqrt(variance_sharpe) * (
            (1.0 - 0.5772156649) * norm_ppf(p1)
            + 0.5772156649 * norm_ppf(p2)
        )

        # Standard deviation of Sharpe Ratio estimate incorporating skewness and kurtosis
        sr_std = math.sqrt(
            (1.0 - (skewness * observed_sharpe) + ((kurtosis - 1.0) / 4.0) * (observed_sharpe ** 2))
            / (sample_length - 1)
        )

        if sr_std <= 0:
            return {"observed_sharpe": observed_sharpe, "dsr_prob": 0.0, "verdict": "REJECTED (Invalid variance)"}

        z_score = (observed_sharpe - e_max_sharpe) / sr_std
        dsr_prob = norm_cdf(z_score)

        verdict = "PASS (DSR > 0.95)" if dsr_prob >= 0.95 else "REJECTED (DSR < 0.95 — Multiple Testing Risk)"

        return {
            "observed_sharpe": round(observed_sharpe, 2),
            "expected_max_sharpe": round(e_max_sharpe, 2),
            "dsr_prob": round(dsr_prob * 100.0, 1),
            "num_trials": num_trials,
            "verdict": verdict,
        }
