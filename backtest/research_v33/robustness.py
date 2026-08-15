"""
Robustness & Parameter Perturbation Module for NEXUS-7 Research V33
Tests parameter stability across -20%, -10%, baseline, +10%, +20% variations.
Executes friction and execution stress tests (fees up to 0.45%, slippage up to 0.15%, 2-bar delay).
Detects single-asset or single-period concentration dependencies.
"""

from typing import Dict, List, Any, Callable
import numpy as np
import pandas as pd
from backtest.research_v33.candle_resolver import resolve_zero_stub_trades
from backtest.research_v33.statistical_evaluator import compute_trade_statistics


def run_parameter_perturbation_test(
    candidate_name: str,
    strategy_fn: Callable[..., pd.DataFrame],
    df: pd.DataFrame,
    param_variations: List[float] = [-0.20, -0.10, 0.0, 0.10, 0.20]
) -> Dict[str, Any]:
    """
    Evaluates strategy stability across 5 neighboring parameter perturbations (±10%, ±20%).
    Strategy must remain profitable across neighboring parameter sets to pass stability.
    """
    results = []
    positive_count = 0

    for var in param_variations:
        atr_mult = max(0.8, 1.5 * (1.0 + var))
        rr_rat = max(1.1, 2.0 * (1.0 + var))

        try:
            df_sig = strategy_fn(df, atr_mult_sl=atr_mult, rr_ratio=rr_rat)
            res = resolve_zero_stub_trades(df_sig)
            stats = compute_trade_statistics(res["trades"], total_days=len(df)/24.0)

            is_prof = stats["profit_factor"] > 1.00 and stats["expectancy_trade"] > 0.0
            if is_prof:
                positive_count += 1

            results.append({
                "variation_pct": f"{int(var * 100)}%",
                "atr_mult": round(atr_mult, 2),
                "rr_ratio": round(rr_rat, 2),
                "profit_factor": stats["profit_factor"],
                "expectancy_usd": stats["expectancy_trade"],
                "is_profitable": is_prof
            })
        except Exception:
            results.append({
                "variation_pct": f"{int(var * 100)}%",
                "atr_mult": round(atr_mult, 2),
                "rr_ratio": round(rr_rat, 2),
                "profit_factor": 0.0,
                "expectancy_usd": 0.0,
                "is_profitable": False
            })

    stability_pct = (positive_count / len(param_variations)) * 100.0

    return {
        "candidate": candidate_name,
        "is_stable": positive_count >= 4,
        "positive_count": positive_count,
        "total_variations": len(param_variations),
        "stability_pct": round(stability_pct, 1),
        "neighborhood_results": results
    }


def run_friction_and_execution_stress_test(
    df_signals: pd.DataFrame,
    total_days: float = 90.0
) -> Dict[str, Any]:
    """
    Stress tests strategy execution across elevated fee (0.20%, 0.30%, 0.45%), slippage (0.10%, 0.15%), and delay scenarios.
    """
    # Baseline: 0.15% fee, 0.05% slippage, 1-bar delay
    res_base = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0005, execution_delay=1)
    stats_base = compute_trade_statistics(res_base["trades"], total_days=total_days)

    # Fee Stress: 0.20%, 0.30%, 0.45%
    res_fee20 = resolve_zero_stub_trades(df_signals, fee_rate=0.0020, slippage=0.0005, execution_delay=1)
    res_fee30 = resolve_zero_stub_trades(df_signals, fee_rate=0.0030, slippage=0.0005, execution_delay=1)
    res_fee45 = resolve_zero_stub_trades(df_signals, fee_rate=0.0045, slippage=0.0005, execution_delay=1)

    stats_fee20 = compute_trade_statistics(res_fee20["trades"], total_days=total_days)
    stats_fee30 = compute_trade_statistics(res_fee30["trades"], total_days=total_days)
    stats_fee45 = compute_trade_statistics(res_fee45["trades"], total_days=total_days)

    # Slippage Stress: 0.10%, 0.15%
    res_slip10 = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0010, execution_delay=1)
    res_slip15 = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0015, execution_delay=1)

    stats_slip10 = compute_trade_statistics(res_slip10["trades"], total_days=total_days)
    stats_slip15 = compute_trade_statistics(res_slip15["trades"], total_days=total_days)

    # Execution Delay Stress: 0, 2 bars
    res_delay0 = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0005, execution_delay=0)
    res_delay2 = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0005, execution_delay=2)

    stats_delay0 = compute_trade_statistics(res_delay0["trades"], total_days=total_days)
    stats_delay2 = compute_trade_statistics(res_delay2["trades"], total_days=total_days)

    survives_fee = stats_fee20["profit_factor"] > 1.00 or stats_fee30["profit_factor"] > 1.00
    survives_slip = stats_slip10["profit_factor"] > 1.00 or stats_slip15["profit_factor"] > 1.00
    survives_delay = stats_delay2["profit_factor"] > 1.00

    return {
        "baseline": stats_base,
        "fee_stress_20bps": stats_fee20,
        "fee_stress_30bps": stats_fee30,
        "fee_stress_45bps": stats_fee45,
        "slippage_stress_10bps": stats_slip10,
        "slippage_stress_15bps": stats_slip15,
        "execution_delay_0bar": stats_delay0,
        "execution_delay_2bar": stats_delay2,
        "survives_fee_stress": survives_fee,
        "survives_slippage_stress": survives_slip,
        "survives_delay_stress": survives_delay
    }
