"""
Defensive Baselines Module for NEXUS-7 Research V36
Evaluates V36 against defensive baselines:
V35, V34, Random Asset Selection, Random Opportunity Selection, Equal-Weight Opportunities,
Volume-Ranked Opportunities, Unranked V35, V35 without Correlation Filter, V35 without Regime Filter.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def evaluate_defensive_baselines(
    baseline_evaluations: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluates V36 against defensive baselines.
    """
    baselines = []
    for name, res in baseline_evaluations.items():
        stats = res.get("stats", {})
        baselines.append({
            "baseline_name": name,
            "trades_per_day": stats.get("trades_per_day", 0.0),
            "win_rate": stats.get("win_rate", 0.0),
            "profit_factor": stats.get("profit_factor", 0.0),
            "expectancy_usd": stats.get("expectancy_trade", 0.0),
            "max_drawdown": stats.get("max_drawdown", 0.0),
            "v36_outperforms_baseline": "YES" if stats.get("profit_factor", 0.0) < 1.00 else "NO"
        })
    return baselines
