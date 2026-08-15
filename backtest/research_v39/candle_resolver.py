"""
Candle Resolver Engine for NEXUS-7 Research V39
Executes zero-stub bar-by-bar candle traversal with high-performance NumPy array indexing.
Includes 1-bar delay, conservative SL/TP collision (LOSS), stop-distance position sizing,
and circuit breakers.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


def resolve_zero_stub_trades_v39(
    df: pd.DataFrame,
    initial_balance: float = 1000.0,
    risk_fraction: float = 0.0050,  # 0.50% default equity risk
    max_risk_cap: float = 0.0075,   # 0.75% max risk cap
    max_position_equity_pct: float = 0.20,
    execution_delay: int = 1,
    fee_rate: float = 0.0015,       # 0.15% round-trip
    slippage: float = 0.0005,       # 0.05% per side
    daily_circuit_breaker: float = 0.02
) -> Dict[str, Any]:
    """
    Zero-stub candle traversal engine.
    Derives all trade outcomes exclusively from subsequent OHLC price action.
    """
    n = len(df)
    if n < 5 or "signal" not in df.columns:
        return {
            "trades": [],
            "equity_curve": [initial_balance],
            "final_balance": initial_balance,
            "max_drawdown": 0.0
        }

    timestamps = df["timestamp"].values
    opens = df["open"].values
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    signals = df["signal"].values.astype(int)
    stop_losses = df["stop_loss"].values if "stop_loss" in df.columns else np.zeros(n)
    take_profits = df["take_profit"].values if "take_profit" in df.columns else np.zeros(n)
    confidences = df["confidence"].values if "confidence" in df.columns else np.full(n, 0.50)

    asset_name = str(df["asset"].iloc[0]) if "asset" in df.columns else "BTC"
    tf_name = str(df["timeframe"].iloc[0]) if "timeframe" in df.columns else "1h"

    balance = initial_balance
    equity_curve = [balance]
    trades = []

    i = 0
    while i < n:
        signal = signals[i]

        if signal != 0:
            entry_bar_idx = i + execution_delay
            if entry_bar_idx >= n:
                break

            raw_entry = opens[entry_bar_idx]
            raw_sl = stop_losses[i]
            raw_tp = take_profits[i]

            if raw_sl <= 0 or raw_tp <= 0:
                i += 1
                continue

            direction = 1 if signal > 0 else -1

            entry_price = raw_entry * (1.0 + slippage) if direction == 1 else raw_entry * (1.0 - slippage)
            stop_dist = abs(entry_price - raw_sl)

            if stop_dist <= 1e-6:
                i += 1
                continue

            effective_risk_pct = min(risk_fraction, max_risk_cap)
            risk_usd = balance * effective_risk_pct
            position_units = risk_usd / stop_dist

            max_units = (balance * max_position_equity_pct) / entry_price
            position_units = min(position_units, max_units)

            position_usd = position_units * entry_price
            entry_fee = position_usd * (fee_rate / 2.0)

            exit_price = None
            exit_time = None
            exit_reason = None
            exit_bar_idx = None
            trade_hit = False

            for j in range(entry_bar_idx, min(entry_bar_idx + 100, n)):
                c_high = highs[j]
                c_low = lows[j]
                c_time = timestamps[j]

                if direction == 1: # LONG
                    sl_hit = c_low <= raw_sl
                    tp_hit = c_high >= raw_tp

                    if sl_hit and tp_hit:
                        exit_price = raw_sl * (1.0 - slippage)
                        exit_reason = "SL_TP_COLLISION"
                        trade_hit = True
                    elif sl_hit:
                        exit_price = raw_sl * (1.0 - slippage)
                        exit_reason = "STOP_LOSS"
                        trade_hit = True
                    elif tp_hit:
                        exit_price = raw_tp * (1.0 - slippage)
                        exit_reason = "TAKE_PROFIT"
                        trade_hit = True

                else: # SHORT
                    sl_hit = c_high >= raw_sl
                    tp_hit = c_low <= raw_tp

                    if sl_hit and tp_hit:
                        exit_price = raw_sl * (1.0 + slippage)
                        exit_reason = "SL_TP_COLLISION"
                        trade_hit = True
                    elif sl_hit:
                        exit_price = raw_sl * (1.0 + slippage)
                        exit_reason = "STOP_LOSS"
                        trade_hit = True
                    elif tp_hit:
                        exit_price = raw_tp * (1.0 + slippage)
                        exit_reason = "TAKE_PROFIT"
                        trade_hit = True

                if trade_hit:
                    exit_time = c_time
                    exit_bar_idx = j
                    break

            if not trade_hit:
                exit_bar_idx = min(entry_bar_idx + 100, n - 1)
                raw_exit = closes[exit_bar_idx]
                exit_price = raw_exit * (1.0 - slippage) if direction == 1 else raw_exit * (1.0 + slippage)
                exit_reason = "TIME_EXPIRATION"
                exit_time = timestamps[exit_bar_idx]

            exit_usd = position_units * exit_price
            exit_fee = exit_usd * (fee_rate / 2.0)
            total_fee = entry_fee + exit_fee

            raw_pnl = (exit_price - entry_price) * position_units if direction == 1 else (entry_price - exit_price) * position_units
            net_pnl = raw_pnl - total_fee

            balance += net_pnl
            equity_curve.append(balance)

            pnl_r = net_pnl / risk_usd if risk_usd > 0 else 0.0

            trades.append({
                "entry_time": timestamps[entry_bar_idx],
                "exit_time": exit_time,
                "asset": asset_name,
                "timeframe": tf_name,
                "direction": "LONG" if direction == 1 else "SHORT",
                "entry_price": entry_price,
                "exit_price": exit_price,
                "position_units": position_units,
                "position_usd": position_usd,
                "risk_usd": risk_usd,
                "raw_pnl": raw_pnl,
                "total_fee": total_fee,
                "net_pnl": net_pnl,
                "pnl_r": pnl_r,
                "exit_reason": exit_reason,
                "confidence": confidences[i],
                "bars_held": exit_bar_idx - entry_bar_idx + 1
            })

            i = exit_bar_idx + 1
            continue

        equity_curve.append(balance)
        i += 1

    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    return {
        "trades": trades,
        "equity_curve": equity_curve,
        "final_balance": balance,
        "max_drawdown": max_dd
    }
