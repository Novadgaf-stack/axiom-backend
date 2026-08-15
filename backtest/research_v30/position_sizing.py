"""
NEXUS-7 Research V30 — Position Sizing Module
Evaluates risk budget tiers (0.25%, 0.50%, 0.75%, 1.00%) strictly calculated from stop distance.
Enforces rule: position size MUST NOT be increased if Profit Factor <= 1.00 or Expectancy <= 0.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd

from backtest.research_v30.candle_resolver import resolve_zero_stub_trades
from backtest.research_v30.statistical_evaluator import compute_trade_statistics


def evaluate_position_sizing_tiers(
    df_signals: pd.DataFrame,
    risk_budgets: List[float] = None
) -> Dict[str, Any]:
    """
    Evaluates 0.25%, 0.50%, 0.75%, and 1.00% position risk budgets on df_signals.
    Checks baseline PF/expectancy before allowing higher risk tiers.
    """
    if risk_budgets is None:
        risk_budgets = [0.0025, 0.0050, 0.0075, 0.0100]

    baseline_res = resolve_zero_stub_trades(df_signals, risk_fraction=0.0050)
    baseline_stats = compute_trade_statistics(baseline_res["trades"])

    pf_baseline = baseline_stats["profit_factor"]
    exp_baseline = baseline_stats["expectancy_trade"]

    # Rule: If PF <= 1.00 or Expectancy <= 0, risk budget must NOT be increased above baseline!
    allow_higher_risk = (pf_baseline > 1.00) and (exp_baseline > 0.0)

    sizing_results = {}
    for rb in risk_budgets:
        if rb > 0.0050 and not allow_higher_risk:
            # Force conservative 0.50% execution if baseline edge is non-positive
            res = resolve_zero_stub_trades(df_signals, risk_fraction=0.0050)
            stats = compute_trade_statistics(res["trades"])
            stats["sizing_note"] = "CAP_ENFORCED (PF <= 1.00)"
        else:
            res = resolve_zero_stub_trades(df_signals, risk_fraction=rb)
            stats = compute_trade_statistics(res["trades"])
            stats["sizing_note"] = "STANDARD_EXECUTION"

        label = f"risk_{int(rb*10000)}bps"
        sizing_results[label] = {
            "risk_fraction": rb,
            "stats": stats,
            "final_balance": res["final_balance"],
            "max_drawdown": res["max_drawdown"]
        }

    return sizing_results
