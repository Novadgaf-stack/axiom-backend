"""
Walk-Forward Validation Module for NEXUS-7 Research V39
Implements 5 to 8 chronological expanding walk-forward windows.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v39.candle_resolver import resolve_zero_stub_trades_v39


def run_expanding_walk_forward_v39(
    df: pd.DataFrame,
    num_windows: int = 6
) -> Dict[str, Any]:
    """
    Executes expanding walk-forward validation across `num_windows` windows.
    """
    n = len(df)
    if n < 100:
        return {
            "window_results": [],
            "positive_windows": 0,
            "total_windows": num_windows,
            "consistency_pct": 0.0
        }

    window_size = n // num_windows
    window_results = []
    positive_count = 0

    for w in range(num_windows):
        start_idx = w * window_size
        end_idx = min(n, (w + 1) * window_size)

        sub_df = df.iloc[start_idx:end_idx].copy().reset_index(drop=True)
        res = resolve_zero_stub_trades_v39(sub_df)
        trades = res["trades"]

        pnls = [t["net_pnl"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]

        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        net_profit = sum(pnls)

        is_positive = pf >= 1.0 and net_profit > 0
        if is_positive:
            positive_count += 1

        window_results.append({
            "window_index": w + 1,
            "trade_count": len(trades),
            "profit_factor": round(pf, 3),
            "net_profit": round(net_profit, 2),
            "is_positive": is_positive
        })

    consistency_pct = (positive_count / num_windows) * 100.0

    return {
        "window_results": window_results,
        "positive_windows": positive_count,
        "total_windows": num_windows,
        "consistency_pct": round(consistency_pct, 1)
    }
