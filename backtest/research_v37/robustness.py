"""
Robustness & Adversarial Overfit Testing Module for NEXUS-7 Research V37
Tests parameter perturbations (+/-5%, +/-10%, +/-20%, +/-30%),
parameter plateau analysis, and adversarial best-trade / best-asset removal tests.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v37.candle_resolver import resolve_zero_stub_trades


def run_parameter_perturbations(
    df: pd.DataFrame,
    strategy_fn: Any,
    base_atr_mult: float = 1.5,
    base_rr: float = 2.0
) -> Dict[str, Any]:
    """
    Tests parameter perturbations (+/-5%, +/-10%, +/-20%, +/-30%) around selected parameters.
    """
    perturbations = [
        ("BASE_00", 1.00),
        ("PLUS_05", 1.05),
        ("MINUS_05", 0.95),
        ("PLUS_10", 1.10),
        ("MINUS_10", 0.90),
        ("PLUS_20", 1.20),
        ("MINUS_20", 0.80),
        ("PLUS_30", 1.30),
        ("MINUS_30", 0.70)
    ]

    configs = {}
    positive_count = 0

    for name, mult in perturbations:
        adj_atr = base_atr_mult * mult
        adj_rr = base_rr * mult

        df_sig = strategy_fn(df, atr_mult_sl=adj_atr, rr_ratio=adj_rr)
        res = resolve_zero_stub_trades(df_sig)
        trades = res["trades"]

        pnls = [t["net_pnl"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]

        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        net_profit = sum(pnls)

        is_positive = pf >= 1.0 and net_profit > 0
        if is_positive:
            positive_count += 1

        configs[name] = {
            "atr_mult": round(adj_atr, 3),
            "rr_ratio": round(adj_rr, 3),
            "profit_factor": round(pf, 3),
            "net_profit": round(net_profit, 2),
            "trade_count": len(trades),
            "is_positive": is_positive
        }

    stability_pct = (positive_count / len(perturbations)) * 100.0

    return {
        "configurations": configs,
        "positive_configurations": positive_count,
        "total_configurations": len(perturbations),
        "stability_pct": round(stability_pct, 1),
        "has_parameter_plateau": stability_pct >= 70.0
    }


def run_best_trade_and_asset_removal_tests(
    trades: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Recalculates Profit Factor after removing best 1, 3, 5, 10% of trades,
    and best single asset.
    """
    if not trades or len(trades) < 5:
        return {
            "remove_best_1_pf": 0.0,
            "remove_best_3_pf": 0.0,
            "remove_best_5_pf": 0.0,
            "remove_best_10pct_pf": 0.0,
            "remove_best_asset_pf": 0.0,
            "trade_removal_passed": False
        }

    sorted_trades = sorted(trades, key=lambda t: t["net_pnl"], reverse=True)
    n = len(sorted_trades)

    def calc_pf(t_list: List[Dict[str, Any]]) -> float:
        pnls = [t["net_pnl"] for t in t_list]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        return sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)

    pf_rem1 = calc_pf(sorted_trades[1:]) if n > 1 else 0.0
    pf_rem3 = calc_pf(sorted_trades[3:]) if n > 3 else 0.0
    pf_rem5 = calc_pf(sorted_trades[5:]) if n > 5 else 0.0
    rem_10pct = max(1, int(n * 0.10))
    pf_rem10pct = calc_pf(sorted_trades[rem_10pct:]) if n > rem_10pct else 0.0

    # Best asset removal
    asset_profits = {}
    for t in trades:
        asset = t["asset"]
        asset_profits[asset] = asset_profits.get(asset, 0.0) + t["net_pnl"]

    if asset_profits:
        best_asset = max(asset_profits, key=asset_profits.get)
        trades_without_best_asset = [t for t in trades if t["asset"] != best_asset]
        pf_rem_asset = calc_pf(trades_without_best_asset)
    else:
        pf_rem_asset = 0.0

    return {
        "remove_best_1_pf": round(pf_rem1, 3),
        "remove_best_3_pf": round(pf_rem3, 3),
        "remove_best_5_pf": round(pf_rem5, 3),
        "remove_best_10pct_pf": round(pf_rem10pct, 3),
        "remove_best_asset_pf": round(pf_rem_asset, 3),
        "trade_removal_passed": bool(pf_rem5 >= 1.0 and pf_rem_asset >= 1.0)
    }
