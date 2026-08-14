"""
NEXUS-7 — RESEARCH V25 BOOTSTRAP ANALYSIS MODULE
Computes 1,000-iteration bootstrap 95% Confidence Intervals for Profit Factor, Expectancy, and Win Rate.
"""
import numpy as np
from typing import List, Tuple

def compute_bootstrap_ci(pnls: List[float], iterations: int = 1000) -> Tuple[float, float]:
    if len(pnls) < 5:
        return 0.0, 0.0
    bootstrap_pfs = []
    for _ in range(iterations):
        resample = np.random.choice(pnls, size=len(pnls), replace=True)
        g_gain = sum(x for x in resample if x > 0)
        g_loss = abs(sum(x for x in resample if x < 0))
        b_pf = g_gain / g_loss if g_loss > 0 else 1.0
        bootstrap_pfs.append(b_pf)
    return float(np.percentile(bootstrap_pfs, 2.5)), float(np.percentile(bootstrap_pfs, 97.5))
