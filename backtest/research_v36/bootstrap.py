"""
Bootstrap Resampling Module for NEXUS-7 Research V36
Executes 5,000-iteration Bootstrap resampling to calculate 95% Confidence Intervals
for Profit Factor, Expectancy, Return, and Win Rate.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def run_bootstrap_resampling(
    trades: List[Dict[str, Any]],
    iterations: int = 5000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Executes 5,000-iteration Bootstrap resampling across trade outcomes.
    """
    if not trades:
        return {
            "iterations": iterations,
            "pf_ci_lower": 0.0,
            "pf_ci_upper": 0.0,
            "exp_ci_lower": 0.0,
            "exp_ci_upper": 0.0,
            "win_rate_ci_lower": 0.0,
            "win_rate_ci_upper": 0.0,
            "passed_bootstrap_gate": False
        }

    pnls = np.array([t["net_pnl"] for t in trades])
    n = len(pnls)
    rng = np.random.default_rng(seed)

    boot_pfs = []
    boot_exps = []
    boot_wrs = []

    for _ in range(iterations):
        sample = rng.choice(pnls, size=n, replace=True)
        w = sample[sample > 0]
        l = sample[sample < 0]
        gp = np.sum(w) if len(w) > 0 else 0.0
        gl = np.abs(np.sum(l)) if len(l) > 0 else 0.0
        pf = gp / gl if gl > 0 else (99.0 if gp > 0 else 0.0)
        boot_pfs.append(pf)
        boot_exps.append(np.mean(sample))
        boot_wrs.append(len(w) / n * 100.0)

    pf_lower = float(np.percentile(boot_pfs, 2.5))
    pf_upper = float(np.percentile(boot_pfs, 97.5))

    exp_lower = float(np.percentile(boot_exps, 2.5))
    exp_upper = float(np.percentile(boot_exps, 97.5))

    wr_lower = float(np.percentile(boot_wrs, 2.5))
    wr_upper = float(np.percentile(boot_wrs, 97.5))

    return {
        "iterations": iterations,
        "pf_ci_lower": round(pf_lower, 3),
        "pf_ci_upper": round(pf_upper, 3),
        "exp_ci_lower": round(exp_lower, 2),
        "exp_ci_upper": round(exp_upper, 2),
        "win_rate_ci_lower": round(wr_lower, 1),
        "win_rate_ci_upper": round(wr_upper, 1),
        "passed_bootstrap_gate": bool(pf_lower > 1.00)
    }
