"""
Candle Resolver Engine for NEXUS-7 Research V37
Executes zero-stub bar-by-bar candle traversal with high-performance NumPy array indexing.
Includes 1-bar delay, 0.15% fees, 0.05% slippage, conservative SL/TP collision (LOSS),
stop-distance position sizing, consecutive-loss step-downs, and circuit breakers.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


def resolve_zero_stub_trades(
    df: pd.DataFrame,
    initial_balance: float = 1000.0,
    risk_fraction: float = 0.0050,  # 0.50% default equity risk
    max_risk_cap: float = 0.0075,   # 0.75% max production risk cap
    max_position_equity_pct: float = 0.20, # 20% max notional per position
    execution_delay: int = 1,
    fee_rate: float = 0.0015,       # 0.15% round-trip (0.075% entry, 0.075% exit)
    slippage: float = 0.0005,       # 0.05% per side
    daily_circuit_breaker: float = 0.02, # 2% daily loss limit
    weekly_circuit_breaker: float = 0.04, # 4% weekly loss limit
    correlation_penalty_mult: float = 1.0
) -> Dict[str, Any]:
    """
    Zero-stub candle traversal engine optimized with NumPy arrays.
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

    consecutive_losses = 0
    paused_for_review = False
    circuit_breaker_tripped = False
    weekly_breaker_tripped = False

    current_day = None
    day_start_balance = balance
    current_week = None
    week_start_balance = balance

    i = 0
    while i < n:
        timestamp = timestamps[i]
        signal = signals[i]

        ts_dt = pd.to_datetime(timestamp)
        day_date = ts_dt.date()
        year_week = (ts_dt.year, ts_dt.isocalendar()[1])

        if current_day != day_date:
            current_day = day_date
            day_start_balance = balance
            circuit_breaker_tripped = False

        if current_week != year_week:
            current_week = year_week
            week_start_balance = balance
            weekly_breaker_tripped = False

        if (day_start_balance - balance) / day_start_balance >= daily_circuit_breaker:
            circuit_breaker_tripped = True

        if (week_start_balance - balance) / week_start_balance >= weekly_circuit_breaker:
            weekly_breaker_tripped = True

        if signal != 0 and not circuit_breaker_tripped and not weekly_breaker_tripped and not paused_for_review:
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

            effective_risk_pct = min(risk_fraction, max_risk_cap) * correlation_penalty_mult
            if consecutive_losses >= 5:
                effective_risk_pct = min(effective_risk_pct, 0.0025)
            if consecutive_losses >= 8:
                paused_for_review = True
                i += 1
                continue

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

            if net_pnl < 0:
                consecutive_losses += 1
            else:
                consecutive_losses = 0

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
        "max_drawdown": max_dd,
        "paused_for_review": paused_for_review
    }
