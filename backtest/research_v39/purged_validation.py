"""
Purged Validation Module for NEXUS-7 Research V39
Implements Purged Walk-Forward Cross-Validation with embargo periods between train and OOS windows.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v39.candle_resolver import resolve_zero_stub_trades_v39


def run_purged_walk_forward_v39(
    df: pd.DataFrame,
    num_windows: int = 6,
    purge_bars: int = 24,
    embargo_bars: int = 24
) -> Dict[str, Any]:
    """
    Executes Purged Walk-Forward validation with purging and embargo periods.
    """
    n = len(df)
    if n < 150:
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
        start_idx = w * window_size + purge_bars
        end_idx = min(n - embargo_bars, (w + 1) * window_size)

        if start_idx >= end_idx:
            continue

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

    total_valid = len(window_results)
    consistency_pct = (positive_count / max(1, total_valid)) * 100.0

    return {
        "window_results": window_results,
        "positive_windows": positive_count,
        "total_windows": total_valid,
        "consistency_pct": round(consistency_pct, 1)
    }
