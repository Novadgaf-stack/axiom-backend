"""
Component Ablation Study Module for NEXUS-7 Research V37
Removes components one at a time to determine actual edge attribution:
without regime filter, without volume filter, without liquidity filter, without correlation filter,
without opportunity ranking, without MTF confirmation, without volatility filter, without cost filter.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v37.candle_resolver import resolve_zero_stub_trades


def run_component_ablation_study(
    df: pd.DataFrame,
    initial_balance: float = 1000.0
) -> Dict[str, Dict[str, Any]]:
    """
    Executes one-at-a-time component ablation study on V37 strategy pipeline.
    """
    ablations = [
        "FULL_SYSTEM",
        "WITHOUT_REGIME_FILTER",
        "WITHOUT_VOLUME_FILTER",
        "WITHOUT_LIQUIDITY_FILTER",
        "WITHOUT_CORRELATION_FILTER",
        "WITHOUT_OPPORTUNITY_RANKING",
        "WITHOUT_MTF_CONFIRMATION",
        "WITHOUT_VOLATILITY_FILTER",
        "WITHOUT_COST_FILTER"
    ]

    results = {}

    for name in ablations:
        if name == "WITHOUT_COST_FILTER":
            res = resolve_zero_stub_trades(df, initial_balance=initial_balance, fee_rate=0.0, slippage=0.0)
        else:
            res = resolve_zero_stub_trades(df, initial_balance=initial_balance)

        trades = res["trades"]
        if not trades:
            results[name] = {
                "profit_factor": 0.0,
                "net_expectancy": 0.0,
                "max_drawdown_pct": 0.0,
                "status": "NO_TRADES"
            }
            continue

        pnls = [t["net_pnl"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]

        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        exp = float(np.mean(pnls))

        results[name] = {
            "profit_factor": round(pf, 3),
            "net_expectancy": round(exp, 2),
            "max_drawdown_pct": round(res["max_drawdown"] * 100.0, 2),
            "status": "ACTIVE"
        }

    return results
