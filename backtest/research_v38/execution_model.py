"""
Execution Model & Friction Stress Module for NEXUS-7 Research V38
Evaluates trade performance under elevated friction models (10, 15, 20, 30, 40, 50, 75, 100 bps)
and calculates exact break-even transaction cost limits.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v38.candle_resolver import resolve_zero_stub_trades_v38


def run_friction_stress_test_v38(
    df: pd.DataFrame,
    initial_balance: float = 1000.0
) -> Dict[str, Dict[str, Any]]:
    """
    Stress tests V38 execution across 8 friction levels (10 bps to 100 bps total friction).
    """
    scenarios = {
        "FRICTION_10_BPS":  {"fee": 0.0007, "slip": 0.0003}, # 10 bps
        "FRICTION_15_BPS":  {"fee": 0.0010, "slip": 0.0005}, # 15 bps
        "FRICTION_20_BPS":  {"fee": 0.0015, "slip": 0.0005}, # 20 bps (Baseline)
        "FRICTION_30_BPS":  {"fee": 0.0020, "slip": 0.0010}, # 30 bps
        "FRICTION_40_BPS":  {"fee": 0.0030, "slip": 0.0010}, # 40 bps
        "FRICTION_50_BPS":  {"fee": 0.0035, "slip": 0.0015}, # 50 bps
        "FRICTION_75_BPS":  {"fee": 0.0055, "slip": 0.0020}, # 75 bps
        "FRICTION_100_BPS": {"fee": 0.0075, "slip": 0.0025}  # 100 bps
    }

    results = {}

    for sc_name, params in scenarios.items():
        res = resolve_zero_stub_trades_v38(
            df,
            initial_balance=initial_balance,
            fee_rate=params["fee"],
            slippage=params["slip"]
        )

        trades = res["trades"]
        if not trades:
            results[sc_name] = {
                "total_friction_bps": round((params["fee"] + params["slip"]) * 10000.0, 1),
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
            "total_friction_bps": round((params["fee"] + params["slip"]) * 10000.0, 1),
            "profit_factor": round(pf, 3),
            "net_expectancy": round(exp, 2),
            "max_drawdown_pct": round(res["max_drawdown"] * 100.0, 2),
            "trade_count": len(trades),
            "status": "SURVIVED" if pf >= 1.0 else "COLLAPSED"
        }

    return results


def calculate_breakeven_friction_v38(
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
        res = resolve_zero_stub_trades_v38(df, initial_balance=initial_balance, fee_rate=mid, slippage=0.0005)
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
