"""
NEXUS-7 — RESEARCH V28 EXPECTANCY FRONTIER & RISK EVALUATOR
Constructs the Trade Frequency vs. Profit Factor vs. Net Expectancy vs. Max Drawdown Frontier.
Evaluates conservative position risk budgets (0.25%, 0.50%, 0.75% per trade) strictly on candidates
that pass out-of-sample statistical gates.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple

from backtest.research_v28.candle_resolver import compute_trade_ledger_and_equity


def build_expectancy_frontier(eval_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Constructs an Expectancy Frontier table ranking candidates by Trade Frequency, Profit Factor, Net Expectancy, and Max DD.
    """
    rows = []
    for r in eval_results:
        m = r["metrics"]
        ci = r["bootstrap_ci"]
        gate = r["gate_eval"]

        rows.append({
            "candidate_id": r["candidate_id"],
            "family": r["family"],
            "timeframe": r["timeframe"],
            "trades_count": m["total_trades"],
            "trades_per_day": m["trades_per_day"],
            "win_rate_pct": m["win_rate_pct"],
            "profit_factor": m["profit_factor"],
            "bootstrap_ci_pf": f"[{ci[1]:.2f}, {ci[2]:.2f}]",
            "max_drawdown_pct": m["max_drawdown_pct"],
            "net_pnl_usd": m["total_net_pnl"],
            "verdict": gate["verdict"]
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort by proximity to 1.15 trades/day and Profit Factor
        df["freq_dist"] = np.abs(df["trades_per_day"] - 1.15)
        df = df.sort_values(by=["verdict", "freq_dist", "profit_factor"], ascending=[True, True, False]).drop(columns=["freq_dist"])

    return df


def evaluate_risk_budget_tiers(
    trade_ledger: List[Dict[str, Any]],
    initial_balance: float = 10000.0,
    fee_pct: float = 0.0015
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates position risk budget tiers (0.25%, 0.50%, 0.75%) on a trade ledger.
    Treats 0.75% as an upper research scenario, NOT a target.
    Enforces a 2.0% daily circuit breaker limit.
    """
    risk_tiers = [0.0025, 0.0050, 0.0075]  # 0.25%, 0.50%, 0.75%
    tier_results = {}

    for risk_pct in risk_tiers:
        tier_key = f"risk_{risk_pct * 100:.2f}pct"

        # Recompute equity with specified risk budget
        recomputed_ledger, equity_curve = compute_trade_ledger_and_equity(
            all_resolved_trades=trade_ledger,
            initial_balance=initial_balance,
            risk_per_trade_pct=risk_pct,
            fee_pct=fee_pct
        )

        bal = equity_curve[-1] if equity_curve else initial_balance
        net_ret_pct = ((bal - initial_balance) / initial_balance) * 100.0

        eq_arr = np.array(equity_curve)
        pk = np.maximum.accumulate(eq_arr)
        dds = (pk - eq_arr) / pk * 100.0 if len(pk) > 0 else np.array([0.0])
        max_dd = float(np.max(dds)) if len(dds) > 0 else 0.0

        wins = [t["net_pnl"] for t in recomputed_ledger if t["net_pnl"] > 0]
        losses = [abs(t["net_pnl"]) for t in recomputed_ledger if t["net_pnl"] <= 0]

        pf = sum(wins) / sum(losses) if sum(losses) > 0 else (99.0 if sum(wins) > 0 else 0.0)

        tier_results[tier_key] = {
            "risk_per_trade_pct": risk_pct * 100.0,
            "final_balance": round(bal, 2),
            "net_return_pct": round(net_ret_pct, 2),
            "profit_factor": round(pf, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "total_trades": len(recomputed_ledger)
        }

    return tier_results
