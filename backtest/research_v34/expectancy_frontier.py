"""
Expectancy Frontier & Multi-Experiment Module for NEXUS-7 Research V34
Runs:
1. Experiment 1: Universe Size + Ranking vs No Ranking across 12, 25, 50, 75, 100, 150 coins.
2. Experiment 2: Selectivity Buckets (Trade Everything vs Top 50%, Top 25%, Top 10%, Top 5, Top 3, Top 2, Top 1).
3. Experiment 3: Frequency vs Expectancy Trade-Off (Is trading less frequently more profitable after friction?).
Constructs Pareto Expectancy Frontier.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def classify_frequency_band(trades_per_day: float) -> str:
    """Maps trades per day to explicit frequency band."""
    if trades_per_day < 0.50:
        return "< 0.50/day"
    elif trades_per_day < 1.00:
        return "0.50-1.00/day"
    elif trades_per_day < 2.00:
        return "1.00-2.00/day"
    elif trades_per_day < 3.00:
        return "2.00-3.00/day"
    elif trades_per_day < 4.00:
        return "3.00-4.00/day"
    else:
        return "4.00+/day"


def evaluate_experiment_1_ranking_impact(
    unranked_evals: Dict[str, Dict[str, Any]],
    ranked_evals: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Experiment 1: Compares Universe Expansion (12 -> 150 assets) with Ranking vs Without Ranking.
    """
    comparison = []

    for tier_name in ["TIER_1", "TIER_2", "TIER_3", "TIER_4", "TIER_5", "TIER_6"]:
        u_res = unranked_evals.get(tier_name, {})
        r_res = ranked_evals.get(tier_name, {})

        u_stats = u_res.get("stats", {})
        r_stats = r_res.get("stats", {})

        comparison.append({
            "universe_tier": tier_name,
            "num_assets": u_res.get("num_assets", 12),
            "unranked_tpd": u_stats.get("trades_per_day", 0.0),
            "unranked_pf": u_stats.get("profit_factor", 0.0),
            "unranked_exp": u_stats.get("expectancy_trade", 0.0),
            "unranked_dd": u_stats.get("max_drawdown", 0.0),
            "ranked_tpd": r_stats.get("trades_per_day", 0.0),
            "ranked_pf": r_stats.get("profit_factor", 0.0),
            "ranked_exp": r_stats.get("expectancy_trade", 0.0),
            "ranked_dd": r_stats.get("max_drawdown", 0.0),
            "ranking_improved_pf": "YES" if r_stats.get("profit_factor", 0.0) > u_stats.get("profit_factor", 0.0) else "NO"
        })

    return comparison


def evaluate_experiment_2_selectivity(
    selectivity_evaluations: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Experiment 2: Evaluates Selectivity Buckets (Trade Everything vs Top 50%, Top 25%, Top 10%, Top 5, Top 3, Top 2, Top 1).
    """
    comparison = []
    for bucket_name, res in selectivity_evaluations.items():
        stats = res.get("stats", {})
        comparison.append({
            "selectivity_bucket": bucket_name,
            "trades_per_day": stats.get("trades_per_day", 0.0),
            "total_trades": stats.get("total_trades", 0),
            "win_rate": stats.get("win_rate", 0.0),
            "profit_factor": stats.get("profit_factor", 0.0),
            "expectancy_usd": stats.get("expectancy_trade", 0.0),
            "max_drawdown": stats.get("max_drawdown", 0.0),
            "selectivity_improved_edge": "YES" if stats.get("profit_factor", 0.0) > 1.00 else "NO"
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

    sorted_table = sorted(frontier_table, key=lambda x: x["robustness_score"], reverse=True)

    best_prof = max(sorted_table, key=lambda x: x["profit_factor"]) if sorted_table else None
    safest_cand = min(sorted_table, key=lambda x: x["max_drawdown"]) if sorted_table else None

    has_robust = any(x["verdict"] == "V34_ROBUST_PROFITABLE_EDGE_FOUND" for x in sorted_table)

    if has_robust:
        overall_verdict = "V34_ROBUST_PROFITABLE_EDGE_FOUND"
    elif any(x["profit_factor"] > 1.00 and x["trades_per_day"] >= 0.3 for x in sorted_table):
        overall_verdict = "V34_PROFITABLE_BUT_NOT_ROBUST"
    else:
        overall_verdict = "V34_NO_ROBUST_PROFITABLE_EDGE"

    return {
        "frontier_table": sorted_table,
        "best_profitable": best_prof,
        "safest_candidate": safest_cand,
        "overall_verdict": overall_verdict
    }
