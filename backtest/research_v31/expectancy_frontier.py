"""
NEXUS-7 Research V31 — Expectancy Frontier Module
Constructs Pareto Profitability-Frequency Frontier showing Frequency vs Expectancy vs Profit Factor vs Drawdown vs Robustness.
Ranks candidate strategies using multi-factor robustness scoring.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def build_expectancy_frontier(
    candidates_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Ranks candidate strategies using multi-factor robustness scoring.
    Identifies Best-in-Class candidates across dimensions.
    """
    if not candidates_results:
        return {
            "frontier_table": [],
            "best_profitable": None,
            "best_frequency": None,
            "best_risk_adjusted": None,
            "best_robust": None,
            "overall_verdict": "NO_ROBUST_PROFITABLE_EDGE_FOUND"
        }

    all_rows = []

    for res in candidates_results:
        c_name = res["candidate_name"]
        tf = res["timeframe"]
        family = res["family"]
        stats = res["stats_baseline"]

        pf = stats["profit_factor"]
        tpd = stats["trades_per_day"]
        exp_usd = stats["expectancy_trade"]
        exp_r = stats["expectancy_r"]
        mdd = stats["max_drawdown"]
        ci_lower = stats["ci_lower"]
        ci_upper = stats["ci_upper"]
        verdict = stats["verdict"]

        in_target_window = (0.8 <= tpd <= 1.5)
        ret_to_dd = (exp_usd / (mdd * 1000.0 + 1e-8)) if mdd > 0 else 0.0

        score = (
            (1.0 if exp_usd > 0 else 0.0) * 10.0 +
            (1.0 if pf >= 1.25 else 0.0) * 5.0 +
            (1.0 if ci_lower > 1.00 else 0.0) * 5.0 +
            (1.0 if in_target_window else 0.0) * 3.0 +
            (1.0 if mdd <= 0.15 else 0.0) * 3.0 +
            (pf * 2.0)
        )

        row = {
            "candidate": c_name,
            "timeframe": tf,
            "family": family,
            "in_target_window": "YES" if in_target_window else "NO",
            "trades_per_day": round(tpd, 2),
            "total_trades": stats["total_trades"],
            "sample_status": stats["sample_status"],
            "win_rate": round(stats["win_rate"] * 100, 1),
            "net_pnl": round(stats["net_pnl"], 2),
            "profit_factor": round(pf, 3),
            "ci_lower": round(ci_lower, 3),
            "ci_upper": round(ci_upper, 3),
            "expectancy_usd": round(exp_usd, 2),
            "expectancy_r": round(exp_r, 3),
            "max_drawdown": round(mdd * 100, 1),
            "ret_to_dd": round(ret_to_dd, 3),
            "score": round(score, 2),
            "verdict": verdict
        }
        all_rows.append(row)

    sorted_score = sorted(all_rows, key=lambda x: x["score"], reverse=True)
    sorted_pf = sorted(all_rows, key=lambda x: x["profit_factor"], reverse=True)

    best_profitable = sorted_pf[0] if sorted_pf else None

    target_freq_rows = [r for r in all_rows if r["in_target_window"] == "YES"]
    sorted_freq = sorted(target_freq_rows, key=lambda x: x["profit_factor"], reverse=True)
    best_frequency = sorted_freq[0] if sorted_freq else (sorted_pf[0] if sorted_pf else None)

    sorted_risk_adj = sorted(all_rows, key=lambda x: x["ret_to_dd"], reverse=True)
    best_risk_adjusted = sorted_risk_adj[0] if sorted_risk_adj else None

    sorted_robust = sorted(all_rows, key=lambda x: x["ci_lower"], reverse=True)
    best_robust = sorted_robust[0] if sorted_robust else None

    if any(r["verdict"] == "FORWARD_PAPER_READY" for r in all_rows):
        overall_verdict = "FORWARD_PAPER_READY"
    elif any(r["verdict"] == "ROBUST_EDGE_FOUND" for r in all_rows):
        overall_verdict = "ROBUST_EDGE_FOUND"
    elif any(r["verdict"] == "PROMISING_BUT_INSUFFICIENT_SAMPLE" for r in all_rows):
        overall_verdict = "PROMISING_BUT_INSUFFICIENT_SAMPLE"
    elif any(r["verdict"] == "FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE" for r in all_rows):
        overall_verdict = "FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE"
    elif any(r["verdict"] == "PROFITABLE_BUT_NOT_ROBUST" for r in all_rows):
        overall_verdict = "PROFITABLE_BUT_NOT_ROBUST"
    else:
        overall_verdict = "NO_ROBUST_PROFITABLE_EDGE_FOUND"

    return {
        "frontier_table": sorted_score,
        "best_profitable": best_profitable,
        "best_frequency": best_frequency,
        "best_risk_adjusted": best_risk_adjusted,
        "best_robust": best_robust,
        "overall_verdict": overall_verdict
    }
