"""
Expectancy Frontier & Universe Expansion Evaluation Module for NEXUS-7 Research V33
Evaluates universe size scaling (12 vs 20 vs 30 vs 50 vs 75+ assets) and constructs Pareto frontier.
Identifies safest, highest expectancy, highest sustainable frequency, and best growth/drawdown candidates.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


FREQUENCY_BANDS = [
    ("< 0.25/day", 0.0, 0.25),
    ("0.25-0.50/day", 0.25, 0.50),
    ("0.50-0.75/day", 0.50, 0.75),
    ("0.75-1.00/day", 0.75, 1.00),
    ("1.00-1.50/day", 1.00, 1.50),
    ("1.50-2.00/day", 1.50, 2.00),
    ("2.00-3.00/day", 2.00, 3.00),
    ("3.00-4.00/day", 3.00, 4.00),
    ("4.00+/day", 4.00, 999.0)
]


def classify_frequency_band(trades_per_day: float) -> str:
    """Maps trades per day to explicit frequency band."""
    for label, min_val, max_val in FREQUENCY_BANDS:
        if min_val <= trades_per_day < max_val:
            return label
    return "4.0+/day"


def evaluate_universe_expansion_impact(
    universe_evaluations: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compares performance, opportunity frequency, expectancy preservation, and drawdown across 12, 20, 30, 50, 75+ asset universes.
    """
    comparison = []

    for tier_name, res in universe_evaluations.items():
        stats = res.get("stats", {})
        comparison.append({
            "universe_tier": tier_name,
            "num_assets": res.get("num_assets", 12),
            "eligible_assets": res.get("eligible_count", 12),
            "rejected_assets": res.get("rejected_count", 0),
            "trades_per_day": stats.get("trades_per_day", 0.0),
            "total_trades": stats.get("total_trades", 0),
            "win_rate": stats.get("win_rate", 0.0),
            "profit_factor": stats.get("profit_factor", 0.0),
            "expectancy_usd": stats.get("expectancy_trade", 0.0),
            "max_drawdown": stats.get("max_drawdown", 0.0),
            "asset_concentration_pct": stats.get("asset_concentration_pct", 0.0),
            "expectancy_preserved": "YES" if stats.get("profit_factor", 0.0) >= 1.00 else "NO"
        })

    return comparison


def build_expectancy_frontier(
    evaluations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Constructs Pareto frontier breakdown and ranks candidates by multi-factor score.
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

        # Multi-factor robustness score
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

    best_prof = max(sorted_table, key=lambda x: x["profit_factor"]) if sorted_table else None
    safest_cand = min(sorted_table, key=lambda x: x["max_drawdown"]) if sorted_table else None

    # Determine overall verdict
    has_paper_ready = any(x["verdict"] == "V33_FORWARD_PAPER_CANDIDATE" for x in sorted_table)
    has_robust = any(x["verdict"] == "ROBUST_EDGE_FOUND" for x in sorted_table)

    if has_paper_ready:
        overall_verdict = "V33_FORWARD_PAPER_CANDIDATE"
    elif has_robust:
        overall_verdict = "ROBUST_EDGE_FOUND"
    elif any(x["profit_factor"] > 1.00 and x["trades_per_day"] >= 0.3 for x in sorted_table):
        overall_verdict = "PROFITABLE_BUT_NOT_ROBUST"
    else:
        overall_verdict = "V33_NO_ROBUST_PROFITABLE_EDGE"

    return {
        "frontier_table": sorted_table,
        "best_profitable": best_prof,
        "safest_candidate": safest_cand,
        "overall_verdict": overall_verdict
    }
