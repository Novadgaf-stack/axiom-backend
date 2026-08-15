"""
Candle Resolver Engine for NEXUS-7 Research V32
Executes zero-stub bar-by-bar candle traversal, 1-bar delay, realistic fees & slippage,
conservative SL/TP collision handling, stop-distance position sizing,
and consecutive-loss & circuit breaker risk controls.
"""

from typing import Dict, List, Any, Optional, Tuple
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
    Zero-stub candle traversal engine.
    Derives all trade outcomes exclusively from subsequent OHLC price action.
    Implements consecutive-loss protections and circuit breakers.
    """
    n = len(df)
    if n < 5 or "signal" not in df.columns:
        return {
            "trades": [],
            "equity_curve": [initial_balance],
            "final_balance": initial_balance,
            "max_drawdown": 0.0
        }

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
        row = df.iloc[i]
        timestamp = row["timestamp"]
        signal = int(row["signal"])

        # Update daily/weekly tracking for circuit breakers
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

            entry_row = df.iloc[entry_bar_idx]
            raw_entry = entry_row["open"]
            raw_sl = row["stop_loss"]
            raw_tp = row["take_profit"]

            if raw_sl <= 0 or raw_tp <= 0:
                i += 1
                continue

            direction = 1 if signal > 0 else -1

            # Entry slippage adjustment
            entry_price = raw_entry * (1.0 + slippage) if direction == 1 else raw_entry * (1.0 - slippage)
            stop_dist = abs(entry_price - raw_sl)

            if stop_dist <= 1e-6:
                i += 1
                continue

            # Consecutive loss risk step-down
            effective_risk_pct = min(risk_fraction, max_risk_cap) * correlation_penalty_mult
            if consecutive_losses >= 5:
                effective_risk_pct = min(effective_risk_pct, 0.0025)  # Step-down to 0.25% after 5 losses
            if consecutive_losses >= 8:
                paused_for_review = True
                i += 1
                continue

            # Position Sizing: Risk_USD = Balance * Risk_Pct -> Units = Risk_USD / Stop_Dist
            risk_usd = balance * effective_risk_pct
            position_units = risk_usd / stop_dist

            # Enforce max position equity cap (notional exposure)
            max_units = (balance * max_position_equity_pct) / entry_price
            position_units = min(position_units, max_units)

            position_usd = position_units * entry_price
            entry_fee = position_usd * (fee_rate / 2.0)

            # Traverse subsequent candles to find SL / TP exit
            exit_price = None
            exit_time = None
            exit_reason = None
            exit_bar_idx = None
            trade_hit = False

            for j in range(entry_bar_idx, min(entry_bar_idx + 100, n)):
                c_row = df.iloc[j]
                c_high = c_row["high"]
                c_low = c_row["low"]
                c_time = c_row["timestamp"]

                if direction == 1: # LONG
                    sl_hit = c_low <= raw_sl
                    tp_hit = c_high >= raw_tp

                    if sl_hit and tp_hit:
                        # Collision handling: conservative LOSS
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
                        # Collision handling: conservative LOSS
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
                # Time-based exit at end of window
                exit_bar_idx = min(entry_bar_idx + 100, n - 1)
                last_row = df.iloc[exit_bar_idx]
                raw_exit = last_row["close"]
                exit_price = raw_exit * (1.0 - slippage) if direction == 1 else raw_exit * (1.0 + slippage)
                exit_reason = "TIME_EXPIRATION"
                exit_time = last_row["timestamp"]

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
                "entry_time": entry_row["timestamp"],
                "exit_time": exit_time,
                "asset": df["asset"].iloc[0] if "asset" in df.columns else "BTC",
                "timeframe": df["timeframe"].iloc[0] if "timeframe" in df.columns else "1h",
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
                "confidence": row.get("confidence", 0.50),
                "bars_held": exit_bar_idx - entry_bar_idx + 1
            })

            # Advance i past trade exit
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
