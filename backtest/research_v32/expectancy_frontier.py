"""
Expectancy Frontier & Pareto Optimization Module for NEXUS-7 Research V32
Constructs frequency band breakdown (<0.5, 0.5-1.0, 1.0-1.5, 1.5-2.0, 2.0-3.0, 3.0-4.0, 4.0+)
and ranks candidates by multi-factor statistical score.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


FREQUENCY_BANDS = [
    ("< 0.5/day", 0.0, 0.5),
    ("0.5-1.0/day", 0.5, 1.0),
    ("1.0-1.5/day", 1.0, 1.5),
    ("1.5-2.0/day", 1.5, 2.0),
    ("2.0-3.0/day", 2.0, 3.0),
    ("3.0-4.0/day", 3.0, 4.0),
    ("4.0+/day", 4.0, 999.0)
]


def classify_frequency_band(trades_per_day: float) -> str:
    """Maps trades per day to explicit frequency band."""
    for label, min_val, max_val in FREQUENCY_BANDS:
        if min_val <= trades_per_day < max_val:
            return label
    return "4.0+/day"


def build_expectancy_frontier(
    evaluations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Constructs Pareto frontier breakdown and ranks candidates by multi-factor score.
    Score = Profit_Factor * 0.35 + Win_Rate * 0.15 + (1 / (1 + Max_DD)) * 0.20 + Min(Trades/Day, 4.0) * 0.15 + (CI_Lower > 1.0) * 0.15
    """
    frontier_table = []

    for ev in evaluations:
        stats = ev["stats_baseline"]
        cand = ev["candidate_name"]
        tf = ev["timeframe"]
        family = ev["family"]
        tpd = stats["trades_per_day"]
        pf = stats["profit_factor"]
        wr = stats["win_rate"]
        exp = stats["expectancy_trade"]
        dd = stats["max_drawdown"]
        ci_lower = stats["ci_lower"]
        ci_upper = stats["ci_upper"]
        verdict = ev["verdict"]

        freq_band = classify_frequency_band(tpd)
        in_preferred_window = "YES" if 1.5 <= tpd <= 4.0 else "NO"

        # Multi-factor score
        score = (
            pf * 0.35 +
            (wr / 100.0) * 0.15 +
            (1.0 / (1.0 + dd / 100.0)) * 0.20 +
            (min(tpd, 4.0) / 4.0) * 0.15 +
            (1.0 if ci_lower > 1.00 else 0.0) * 0.15
        )

        frontier_table.append({
            "candidate": cand,
            "timeframe": tf,
            "family": family,
            "freq_band": freq_band,
            "in_preferred_window": in_preferred_window,
            "trades_per_day": tpd,
            "win_rate": wr,
            "profit_factor": pf,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "expectancy_usd": exp,
            "max_drawdown": dd,
            "verdict": verdict,
            "robustness_score": round(score, 3)
        })

    # Sort candidates by robustness score descending
    sorted_table = sorted(frontier_table, key=lambda x: x["robustness_score"], reverse=True)

    # Determine leading candidates
    best_prof = max(sorted_table, key=lambda x: x["profit_factor"]) if sorted_table else None
    best_freq_in_window = [x for x in sorted_table if x["in_preferred_window"] == "YES" and x["profit_factor"] > 1.00]
    leading_window_cand = max(best_freq_in_window, key=lambda x: x["trades_per_day"]) if best_freq_in_window else None

    # Overall verdict
    has_paper_ready = any(x["verdict"] == "FORWARD_PAPER_READY" for x in sorted_table)
    has_robust = any(x["verdict"] == "ROBUST_EDGE_FOUND" for x in sorted_table)
    has_freq_unprof = any(x["verdict"] == "FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE" for x in sorted_table)

    if has_paper_ready:
        overall_verdict = "FORWARD_PAPER_READY"
    elif has_robust:
        overall_verdict = "ROBUST_EDGE_FOUND"
    elif has_freq_unprof and not any(x["profit_factor"] >= 1.25 for x in sorted_table):
        overall_verdict = "FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE"
    elif any(x["profit_factor"] > 1.00 for x in sorted_table):
        overall_verdict = "PROFITABLE_BUT_NOT_ROBUST"
    else:
        overall_verdict = "NO_ROBUST_PROFITABLE_EDGE_FOUND"

    return {
        "frontier_table": sorted_table,
        "best_profitable": best_prof,
        "best_frequency_in_window": leading_window_cand,
        "overall_verdict": overall_verdict
    }
