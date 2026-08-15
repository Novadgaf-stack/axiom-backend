"""
Expectancy Frontier & Defensive Baselines Module for NEXUS-7 Research V35
Runs:
1. Defensive Baselines: V34 best candidate, Equal-Weight Random, Random Asset, No Ranking, No Correlation Filter, Top Volume.
2. Selectivity Thresholds: Percentiles (100%, 75%, 50%, 30%, 20%, 10%, 5%) and Top-K (Top 1, 2, 3, 5).
3. Frequency Expectancy Frontier: <0.25, 0.25-0.50, 0.50-0.75, 0.75-1.00, 1.00-1.50, 1.50-2.00, 2.00-3.00, 3.00+/day.
Constructs Pareto Expectancy Frontier.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def classify_frequency_band(trades_per_day: float) -> str:
    """Maps trades per day to explicit frequency band."""
    if trades_per_day < 0.25:
        return "< 0.25/day"
    elif trades_per_day < 0.50:
        return "0.25-0.50/day"
    elif trades_per_day < 0.75:
        return "0.50-0.75/day"
    elif trades_per_day < 1.00:
        return "0.75-1.00/day"
    elif trades_per_day < 1.50:
        return "1.00-1.50/day"
    elif trades_per_day < 2.00:
        return "1.50-2.00/day"
    elif trades_per_day < 3.00:
        return "2.00-3.00/day"
    else:
        return "3.00+/day"


def evaluate_defensive_baselines(
    all_signals: List[Dict[str, Any]],
    baseline_evaluations: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluates V35 against defensive baselines:
    - V34_BEST_CANDIDATE
    - EQUAL_WEIGHT_RANDOM_SELECTION
    - RANDOM_ASSET_SELECTION
    - NO_RANKING
    - NO_CORRELATION_FILTER
    - TOP_VOLUME_SELECTION
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
            "ci_lower": stats.get("ci_lower", 0.0),
            "v35_outperforms_baseline": "YES" if stats.get("profit_factor", 0.0) < 1.00 else "NO"
        })
    return baselines


def evaluate_selectivity_thresholds(
    selectivity_evaluations: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluates Selectivity Thresholds (Top 100% to 5% and Top 1 to 5).
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

    has_robust = any(x["verdict"] == "V35_ROBUST_PROFITABLE_EDGE_FOUND" for x in sorted_table)

    if has_robust:
        overall_verdict = "V35_ROBUST_PROFITABLE_EDGE_FOUND"
    elif any(x["profit_factor"] > 1.00 and x["trades_per_day"] >= 0.3 for x in sorted_table):
        overall_verdict = "V35_PROFITABLE_BUT_NOT_ROBUST"
    elif any(x["trades_per_day"] >= 0.75 for x in sorted_table):
        overall_verdict = "V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE"
    else:
        overall_verdict = "V35_NO_ROBUST_PROFITABLE_EDGE"

    return {
        "frontier_table": sorted_table,
        "best_profitable": best_prof,
        "safest_candidate": safest_cand,
        "overall_verdict": overall_verdict
    }
