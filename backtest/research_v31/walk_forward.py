"""
NEXUS-7 Research V31 — Walk-Forward Validation Module
Executes rolling chronological walk-forward validation across sequential market windows.
Requires >= 3/4 positive OOS windows for robust candidate promotion.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd

from backtest.research_v31.candle_resolver import resolve_zero_stub_trades
from backtest.research_v31.statistical_evaluator import compute_trade_statistics


def run_walk_forward_validation(
    df_signals: pd.DataFrame,
    num_windows: int = 4
) -> Dict[str, Any]:
    """
    Splits df_signals into num_windows chronological segments and evaluates OOS performance on each.
    """
    n = len(df_signals)
    segment_size = n // num_windows

    window_results = []
    positive_windows = 0

    for w in range(num_windows):
        start_idx = w * segment_size
        end_idx = (w + 1) * segment_size if w < num_windows - 1 else n

        sub_df = df_signals.iloc[start_idx:end_idx].copy().reset_index(drop=True)
        res = resolve_zero_stub_trades(sub_df, risk_fraction=0.0050)
        stats = compute_trade_statistics(res["trades"], total_days=90.0 / num_windows)

        if stats["expectancy_trade"] > 0 and stats["profit_factor"] > 1.0:
            positive_windows += 1

        window_results.append({
            "window_index": w + 1,
            "start_time": str(sub_df["timestamp"].iloc[0]),
            "end_time": str(sub_df["timestamp"].iloc[-1]),
            "total_trades": stats["total_trades"],
            "profit_factor": round(stats["profit_factor"], 3),
            "net_pnl": round(stats["net_pnl"], 2),
            "max_drawdown": round(stats["max_drawdown"] * 100, 1),
            "verdict": stats["verdict"]
        })

    consistency_pct = (positive_windows / num_windows) * 100.0
    is_robust_walk_forward = (positive_windows >= 3)

    return {
        "num_windows": num_windows,
        "positive_windows": positive_windows,
        "consistency_pct": round(consistency_pct, 1),
        "is_robust_walk_forward": is_robust_walk_forward,
        "window_results": window_results
    }
