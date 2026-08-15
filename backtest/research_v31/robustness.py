"""
NEXUS-7 Research V31 — Robustness Testing Module
Provides neighboring parameter stability testing (-10%, -5%, baseline, +5%, +10%),
friction stress testing (0.15%, 0.20%, 0.30%), and execution stress testing (delays, missed signals).
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd

from backtest.research_v31.candle_resolver import resolve_zero_stub_trades
from backtest.research_v31.statistical_evaluator import compute_trade_statistics


def run_parameter_perturbation_test(
    candidate_name: str,
    generator_func: Any,
    df_data: pd.DataFrame,
    param_mults: List[float] = None
) -> Dict[str, Any]:
    """
    Evaluates strategy performance across neighboring parameter variations (-10%, -5%, baseline, +5%, +10%).
    Verifies edge is stable across broad parameter regions rather than an isolated peak.
    """
    if param_mults is None:
        param_mults = [0.90, 0.95, 1.00, 1.05, 1.10]

    mult_results = []
    positive_count = 0

    for m in param_mults:
        df_sig = generator_func(df_data.copy(), param_mult=m)
        res = resolve_zero_stub_trades(df_sig, risk_fraction=0.0050)
        stats = compute_trade_statistics(res["trades"])

        if stats["profit_factor"] > 1.0 and stats["expectancy_trade"] > 0:
            positive_count += 1

        mult_results.append({
            "param_mult": m,
            "profit_factor": round(stats["profit_factor"], 3),
            "net_pnl": round(stats["net_pnl"], 2),
            "trades_per_day": round(stats["trades_per_day"], 2),
            "max_drawdown": round(stats["max_drawdown"] * 100, 1)
        })

    is_stable = (positive_count >= 4)

    return {
        "candidate": candidate_name,
        "is_stable": is_stable,
        "positive_count": positive_count,
        "total_tested": len(param_mults),
        "neighborhood_results": mult_results
    }


def run_friction_and_execution_stress_test(
    df_signals: pd.DataFrame
) -> Dict[str, Any]:
    """
    Evaluates strategy under elevated fees (0.20%, 0.30%), elevated slippage (0.10%),
    2-bar execution delay, and 10%-20% missed signals.
    """
    res_base = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0005, execution_delay=1)
    stats_base = compute_trade_statistics(res_base["trades"])

    res_fee20 = resolve_zero_stub_trades(df_signals, fee_rate=0.0020, slippage=0.0005, execution_delay=1)
    stats_fee20 = compute_trade_statistics(res_fee20["trades"])

    res_fee30 = resolve_zero_stub_trades(df_signals, fee_rate=0.0030, slippage=0.0005, execution_delay=1)
    stats_fee30 = compute_trade_statistics(res_fee30["trades"])

    res_slip10 = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0010, execution_delay=1)
    stats_slip10 = compute_trade_statistics(res_slip10["trades"])

    res_delay2 = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0005, execution_delay=2)
    stats_delay2 = compute_trade_statistics(res_delay2["trades"])

    res_missed15 = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0005, execution_delay=1, missed_signal_pct=0.15)
    stats_missed15 = compute_trade_statistics(res_missed15["trades"])

    return {
        "baseline_15bps": stats_base,
        "fee_stress_20bps": stats_fee20,
        "fee_stress_30bps": stats_fee30,
        "slippage_stress_10bps": stats_slip10,
        "delay_stress_2bar": stats_delay2,
        "missed_signals_15pct": stats_missed15
    }
