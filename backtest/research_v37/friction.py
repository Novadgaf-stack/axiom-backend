"""
Friction & Stress Testing Module for NEXUS-7 Research V37
Evaluates trade performance under elevated friction models (0.15%, 0.20%, 0.30%, 0.40%, 0.50% fee rates)
and calculates exact break-even transaction cost limits.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v37.candle_resolver import resolve_zero_stub_trades


def run_friction_stress_test(
    df: pd.DataFrame,
    initial_balance: float = 1000.0
) -> Dict[str, Dict[str, Any]]:
    """
    Stress tests V37 execution across fee & slippage levels:
    - BASELINE: 0.15% fee, 0.05% slippage
    - STRESS_020: 0.20% fee, 0.05% slippage
    - STRESS_030: 0.30% fee, 0.10% slippage
    - STRESS_040: 0.40% fee, 0.15% slippage
    - STRESS_050: 0.50% fee, 0.20% slippage
    """
    scenarios = {
        "BASELINE_015": {"fee": 0.0015, "slip": 0.0005},
        "STRESS_020":   {"fee": 0.0020, "slip": 0.0005},
        "STRESS_030":   {"fee": 0.0030, "slip": 0.0010},
        "STRESS_040":   {"fee": 0.0040, "slip": 0.0015},
        "STRESS_050":   {"fee": 0.0050, "slip": 0.0020}
    }

    results = {}

    for sc_name, params in scenarios.items():
        res = resolve_zero_stub_trades(
            df,
            initial_balance=initial_balance,
            fee_rate=params["fee"],
            slippage=params["slip"]
        )

        trades = res["trades"]
        if not trades:
            results[sc_name] = {
                "profit_factor": 0.0,
                "net_expectancy": 0.0,
                "max_drawdown_pct": 0.0,
                "trade_count": 0,
                "status": "NO_TRADES"
            }
            continue

        pnls = [t["net_pnl"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]

        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        exp = float(np.mean(pnls))

        results[sc_name] = {
            "fee_rate_pct": params["fee"] * 100.0,
            "slippage_pct": params["slip"] * 100.0,
            "profit_factor": round(pf, 3),
            "net_expectancy": round(exp, 2),
            "max_drawdown_pct": round(res["max_drawdown"] * 100.0, 2),
            "trade_count": len(trades),
            "status": "SURVIVED" if pf >= 1.0 else "COLLAPSED"
        }

    return results


def calculate_breakeven_friction(
    df: pd.DataFrame,
    initial_balance: float = 1000.0
) -> float:
    """
    Finds the exact total fee rate (in bps) where Profit Factor drops below 1.00.
    """
    left = 0.0005
    right = 0.0100
    breakeven = 0.0015

    for _ in range(10):
        mid = (left + right) / 2.0
        res = resolve_zero_stub_trades(df, initial_balance=initial_balance, fee_rate=mid, slippage=0.0005)
        trades = res["trades"]
        if not trades:
            break
        pnls = [t["net_pnl"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)

        if pf >= 1.0:
            breakeven = mid
            left = mid
        else:
            right = mid

    return round(breakeven * 10000.0, 1) # basis points
