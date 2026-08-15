"""
NEXUS-7 Research V29 — Expectancy Frontier Module
Constructs Frequency vs Expectancy vs Drawdown Frontier, multi-friction analysis,
risk budget evaluations, and candidate ranking.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd

from backtest.research_v29.candle_resolver import resolve_zero_stub_trades
from backtest.research_v29.statistical_evaluator import compute_trade_statistics


def build_expectancy_frontier(
    candidates_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Ranks candidate strategies and identifies best performers across dimensions:
    - BEST PROFITABLE CANDIDATE (Highest Profit Factor)
    - BEST FREQUENCY CANDIDATE (Highest Trades/Day in target window)
    - BEST RISK-ADJUSTED CANDIDATE (Highest Return-to-Drawdown ratio)
    - BEST ROBUST CANDIDATE (Highest CI lower bound)
    """
    if not candidates_results:
        return {
            "frontier_table": [],
            "best_profitable": None,
            "best_frequency": None,
            "best_risk_adjusted": None,
            "best_robust": None,
            "overall_verdict": "NO ROBUST PROFITABLE EDGE FOUND"
        }

    valid_candidates = []
    all_rows = []

    for res in candidates_results:
        c_name = res["candidate_name"]
        tf = res["timeframe"]
        stats = res["stats_0.15_fee"]

        pf = stats["profit_factor"]
        tpd = stats["trades_per_day"]
        exp_usd = stats["expectancy_trade"]
        exp_r = stats["expectancy_r"]
        mdd = stats["max_drawdown"]
        ci_lower = stats["ci_lower"]
        ci_upper = stats["ci_upper"]
        verdict = stats["verdict"]

        in_target_window = (0.8 <= tpd <= 1.8)
        ret_to_dd = (exp_usd / (mdd * 1000.0 + 1e-8)) if mdd > 0 else 0.0

        row = {
            "candidate": c_name,
            "timeframe": tf,
            "in_target_window": "YES" if in_target_window else "NO",
            "trades_per_day": round(tpd, 2),
            "total_trades": stats["total_trades"],
            "win_rate": round(stats["win_rate"] * 100, 1),
            "net_pnl": round(stats["net_pnl"], 2),
            "profit_factor": round(pf, 3),
            "ci_lower": round(ci_lower, 3),
            "ci_upper": round(ci_upper, 3),
            "expectancy_usd": round(exp_usd, 2),
            "expectancy_r": round(exp_r, 3),
            "max_drawdown": round(mdd * 100, 1),
            "ret_to_dd": round(ret_to_dd, 3),
            "verdict": verdict
        }
        all_rows.append(row)

        if verdict == "GATE_PASSED":
            valid_candidates.append(row)

    # Rank Best Candidates
    sorted_pf = sorted(all_rows, key=lambda x: x["profit_factor"], reverse=True)
    best_profitable = sorted_pf[0] if sorted_pf else None

    # Best frequency in target window [0.8, 1.8]
    freq_in_window = [r for r in all_rows if r["in_target_window"] == "YES"]
    sorted_freq = sorted(freq_in_window, key=lambda x: x["trades_per_day"], reverse=True)
    best_frequency = sorted_freq[0] if sorted_freq else (sorted_pf[0] if sorted_pf else None)

    # Best risk-adjusted
    sorted_risk_adj = sorted(all_rows, key=lambda x: x["ret_to_dd"], reverse=True)
    best_risk_adjusted = sorted_risk_adj[0] if sorted_risk_adj else None

    # Best robust (ci_lower)
    sorted_robust = sorted(all_rows, key=lambda x: x["ci_lower"], reverse=True)
    best_robust = sorted_robust[0] if sorted_robust else None

    if valid_candidates:
        overall_verdict = "CANDIDATE FOUND — REQUIRES FORWARD PAPER VALIDATION"
    else:
        overall_verdict = "NO ROBUST PROFITABLE EDGE FOUND"

    return {
        "frontier_table": all_rows,
        "best_profitable": best_profitable,
        "best_frequency": best_frequency,
        "best_risk_adjusted": best_risk_adjusted,
        "best_robust": best_robust,
        "overall_verdict": overall_verdict
    }


def evaluate_friction_and_risk_budget_sensitivity(
    candidate_name: str,
    oos_data: pd.DataFrame,
    risk_budgets: List[float] = None,
    fee_tiers: List[float] = None
) -> Dict[str, Any]:
    """Evaluates multi-friction (0.15%, 0.30%, 0.45%) and risk budget sensitivity."""
    if risk_budgets is None:
        risk_budgets = [0.0025, 0.0050, 0.0075, 0.0100] # 0.25%, 0.50%, 0.75%, 1.00%
    if fee_tiers is None:
        fee_tiers = [0.0015, 0.0030, 0.0045] # 0.15%, 0.30%, 0.45%

    results_by_fee = {}
    for fee in fee_tiers:
        fee_res = resolve_zero_stub_trades(
            df=oos_data,
            risk_fraction=0.0050,
            fee_rate=fee,
            slippage=0.0005
        )
        stats = compute_trade_statistics(fee_res["trades"])
        results_by_fee[f"fee_{int(fee*10000)}bps"] = stats

    results_by_risk = {}
    for rb in risk_budgets:
        rb_res = resolve_zero_stub_trades(
            df=oos_data,
            risk_fraction=rb,
            fee_rate=0.0015,
            slippage=0.0005
        )
        stats = compute_trade_statistics(rb_res["trades"])
        results_by_risk[f"risk_{int(rb*10000)}bps"] = stats

    return {
        "candidate": candidate_name,
        "friction_sensitivity": results_by_fee,
        "risk_budget_sensitivity": results_by_risk
    }
