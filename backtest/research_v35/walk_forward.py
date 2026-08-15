"""
Walk-Forward Validation Module for NEXUS-7 Research V35
Runs 5-window chronological rolling walk-forward validation with purging and embargoing.
Requires >= 3/5 positive windows for statistical promotion.
"""

from typing import Dict, List, Any, Callable
import numpy as np
import pandas as pd
from backtest.research_v35.candle_resolver import resolve_zero_stub_trades
from backtest.research_v35.statistical_evaluator import compute_trade_statistics


def run_walk_forward_validation(
    df: pd.DataFrame,
    strategy_fn: Callable[[pd.DataFrame], pd.DataFrame],
    num_windows: int = 5,
    embargo_bars: int = 12,
    execution_delay: int = 1
) -> Dict[str, Any]:
    """
    Executes 5-window chronological rolling walk-forward evaluation with purging/embargoing.
    """
    n = len(df)
    window_size = n // num_windows
    if window_size < 20:
        return {"positive_windows": 0, "num_windows": num_windows, "pass_gate": False, "window_results": []}

    window_results = []
    positive_count = 0

    for w in range(num_windows):
        w_start = w * window_size + (embargo_bars if w > 0 else 0)
        w_end = (w + 1) * window_size if w < num_windows - 1 else n
        if w_start >= w_end:
            continue

        df_win = df.iloc[w_start:w_end].copy()

        df_sig = strategy_fn(df_win)
        res = resolve_zero_stub_trades(df_sig, execution_delay=execution_delay)
        stats = compute_trade_statistics(res["trades"], total_days=len(df_win) / 24.0)

        is_prof = stats["profit_factor"] > 1.00 and stats["expectancy_trade"] > 0.0
        if is_prof:
            positive_count += 1

        window_results.append({
            "window_idx": w + 1,
            "num_bars": len(df_win),
            "trades": stats["total_trades"],
            "trades_per_day": stats["trades_per_day"],
            "profit_factor": stats["profit_factor"],
            "expectancy_usd": stats["expectancy_trade"],
            "max_drawdown": stats["max_drawdown"],
            "is_profitable": is_prof
        })

    pass_gate = (positive_count / num_windows) >= 0.60

    return {
        "positive_windows": positive_count,
        "num_windows": num_windows,
        "pass_gate": pass_gate,
        "window_results": window_results
    }
