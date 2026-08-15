"""
Candle Resolver Module for NEXUS-7 Final Master Research
100% zero-stub, deterministic candle-by-candle traversal execution engine.
Simulates trade resolution bar-by-bar from signal timestamp T to exit timestamp T_exit.
Enforces 1-bar execution delay, round-trip fees (0.15%), slippage (0.05% per side),
and conservative SL/TP collision handling (treated as LOSS).
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


def resolve_single_opportunity_final(
    opp: Dict[str, Any],
    df: pd.DataFrame,
    execution_delay: int = 1,
    fee_rate: float = 0.0015,
    slippage_rate: float = 0.0005,
    initial_equity: float = 10000.0,
    risk_pct: float = 0.0050
) -> Optional[Dict[str, Any]]:
    """
    Traverses OHLCV bars sequentially from signal bar index.
    """
    signal_ts = pd.to_datetime(opp["timestamp"])

    ts_series = pd.to_datetime(df["timestamp"])
    matches = df[ts_series == signal_ts]
    if matches.empty:
        return None

    sig_idx = matches.index[0]
    exec_idx = sig_idx + execution_delay
    if exec_idx >= len(df):
        return None

    direction = opp["direction"]
    signal_entry = opp["entry_price"]
    stop_loss = opp["stop_loss"]
    take_profit = opp["take_profit"]

    raw_exec_price = df["open"].iloc[exec_idx]
    if direction == "LONG":
        actual_entry = raw_exec_price * (1.0 + slippage_rate)
    else:
        actual_entry = raw_exec_price * (1.0 - slippage_rate)

    stop_dist = abs(actual_entry - stop_loss)
    if stop_dist <= 0:
        return None

    risk_amount = initial_equity * risk_pct
    position_units = risk_amount / stop_dist
    position_size_usd = position_units * actual_entry

    entry_fee = position_size_usd * fee_rate

    exit_idx = None
    exit_price = None
    exit_reason = None
    bar_duration = 0

    for i in range(exec_idx, len(df)):
        bar_high = df["high"].iloc[i]
        bar_low = df["low"].iloc[i]
        bar_close = df["close"].iloc[i]

        if direction == "LONG":
            hit_sl = bar_low <= stop_loss
            hit_tp = bar_high >= take_profit

            if hit_sl and hit_tp:
                exit_idx = i
                exit_price = stop_loss * (1.0 - slippage_rate)
                exit_reason = "SAME_CANDLE_COLLISION_LOSS"
                break
            elif hit_sl:
                exit_idx = i
                exit_price = stop_loss * (1.0 - slippage_rate)
                exit_reason = "STOP_LOSS"
                break
            elif hit_tp:
                exit_idx = i
                exit_price = take_profit * (1.0 - slippage_rate)
                exit_reason = "TAKE_PROFIT"
                break

        else: # SHORT
            hit_sl = bar_high >= stop_loss
            hit_tp = bar_low <= take_profit

            if hit_sl and hit_tp:
                exit_idx = i
                exit_price = stop_loss * (1.0 + slippage_rate)
                exit_reason = "SAME_CANDLE_COLLISION_LOSS"
                break
            elif hit_sl:
                exit_idx = i
                exit_price = stop_loss * (1.0 + slippage_rate)
                exit_reason = "STOP_LOSS"
                break
            elif hit_tp:
                exit_idx = i
                exit_price = take_profit * (1.0 + slippage_rate)
                exit_reason = "TAKE_PROFIT"
                break

    if exit_idx is None:
        exit_idx = len(df) - 1
        raw_exit = df["close"].iloc[exit_idx]
        exit_price = raw_exit * (1.0 - slippage_rate) if direction == "LONG" else raw_exit * (1.0 + slippage_rate)
        exit_reason = "END_OF_DATA"

    bar_duration = exit_idx - exec_idx + 1
    exit_ts = df["timestamp"].iloc[exit_idx]

    exit_size_usd = position_units * exit_price
    exit_fee = exit_size_usd * fee_rate
    total_fees = entry_fee + exit_fee

    if direction == "LONG":
        gross_pnl = (exit_price - actual_entry) * position_units
    else:
        gross_pnl = (actual_entry - exit_price) * position_units

    net_pnl = gross_pnl - total_fees
    net_return_pct = net_pnl / initial_equity
    r_multiple = net_pnl / risk_amount if risk_amount > 0 else 0.0

    return {
        "signal_timestamp": str(signal_ts),
        "execution_timestamp": str(df["timestamp"].iloc[exec_idx]),
        "exit_timestamp": str(exit_ts),
        "asset": opp["asset"],
        "strategy_family": opp["strategy_family"],
        "direction": direction,
        "execution_delay_bars": execution_delay,
        "entry_price": round(float(actual_entry), 4),
        "exit_price": round(float(exit_price), 4),
        "stop_loss": round(float(stop_loss), 4),
        "take_profit": round(float(take_profit), 4),
        "position_units": round(float(position_units), 6),
        "position_size_usd": round(float(position_size_usd), 2),
        "gross_pnl": round(float(gross_pnl), 4),
        "total_fees": round(float(total_fees), 4),
        "net_pnl": round(float(net_pnl), 4),
        "net_return_pct": round(float(net_return_pct), 6),
        "r_multiple": round(float(r_multiple), 3),
        "exit_reason": exit_reason,
        "bar_duration": bar_duration,
        "market_regime": opp.get("market_regime", "BULL"),
        "volatility_state": opp.get("volatility_state", "NORMAL"),
        "opportunity_score": opp.get("opportunity_score", 0.70)
    }
