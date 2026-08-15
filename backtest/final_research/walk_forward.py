"""
Walk-Forward Validation Module for NEXUS-7 Final Master Research
Chronological expanding walk-forward validation (6+ windows).
Evaluates OOS profit factor, win rate, expectancy, and window consistency.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def run_walk_forward_validation_final(
    df: pd.DataFrame,
    strategy_fn: Any,
    resolver_fn: Any,
    num_windows: int = 6,
    initial_train_pct: float = 0.40
) -> Dict[str, Any]:
    """
    Executes expanding walk-forward validation across 6 chronological windows.
    """
    n = len(df)
    if n < 50:
        return {"positive_windows": 0, "total_windows": num_windows, "consistency_pct": 0.0, "windows": []}

    train_end_initial = int(n * initial_train_pct)
    remaining_bars = n - train_end_initial
    step_size = remaining_bars // num_windows

    windows = []
    positive_windows = 0

    for w in range(num_windows):
        val_start = train_end_initial + w * step_size
        val_end = min(n, val_start + step_size) if w < num_windows - 1 else n

        train_sub = df.iloc[:val_start].copy().reset_index(drop=True)
        val_sub = df.iloc[val_start:val_end].copy().reset_index(drop=True)

        if len(val_sub) < 10:
            continue

        opps = []
        df_sig = strategy_fn(val_sub)
        non_zero = df_sig[df_sig["signal"] != 0]

        for idx, row in non_zero.iterrows():
            opps.append({
                "timestamp": row["timestamp"],
                "asset": "BTC",
                "strategy_family": "trend",
                "direction": "LONG" if row["signal"] == 1 else "SHORT",
                "entry_price": float(row["close"]),
                "stop_loss": float(row["stop_loss"]),
                "take_profit": float(row["take_profit"]),
                "confidence": float(row.get("confidence", 0.50))
            })

        w_trades = []
        for opp in opps:
            t = resolver_fn(opp, val_sub)
            if t is not None:
                w_trades.append(t)

        pnls = [t["net_pnl"] for t in w_trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]

        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        net_profit = sum(pnls)

        if pf > 1.0 and net_profit > 0.0:
            positive_windows += 1

        windows.append({
            "window_index": w + 1,
            "val_start_ts": str(val_sub["timestamp"].iloc[0]),
            "val_end_ts": str(val_sub["timestamp"].iloc[-1]),
            "trade_count": len(w_trades),
            "profit_factor": round(float(pf), 3),
            "net_profit": round(float(net_profit), 2)
        })

    consistency_pct = (positive_windows / len(windows) * 100.0) if windows else 0.0

    return {
        "positive_windows": positive_windows,
        "total_windows": len(windows),
        "consistency_pct": round(consistency_pct, 1),
        "windows": windows
    }
