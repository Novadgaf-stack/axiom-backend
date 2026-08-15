"""
NEXUS-7 Research V29 — Zero-Stub Candle Traversal Resolver Module
Derives trade outcomes strictly from bar-by-bar candle traversal.
Handles execution delay, fees, slippage, conservative same-candle SL/TP collisions,
stop-distance position sizing, portfolio daily circuit breaker, and asset correlation limits.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


def resolve_zero_stub_trades(
    df: pd.DataFrame,
    risk_fraction: float = 0.005,  # 0.50% account risk per trade
    fee_rate: float = 0.0015,      # 0.15% roundtrip fee
    slippage: float = 0.0005,      # 0.05% per side
    execution_delay: int = 1,      # 1-bar execution delay
    initial_balance: float = 1000.0,
    daily_circuit_breaker: float = 0.02, # 2% daily loss limit
    max_position_equity_pct: float = 0.20,
    correlation_penalty_mult: float = 1.0
) -> Dict[str, Any]:
    """
    Executes bar-by-bar zero-stub candle traversal for signals in df.
    Returns trade ledger, equity curve, and summary statistics.
    """
    n = len(df)
    if n < 50 or "signal" not in df.columns:
        return {
            "trades": [],
            "equity_curve": [initial_balance],
            "final_balance": initial_balance,
            "max_drawdown": 0.0
        }

    balance = initial_balance
    equity_curve = [balance]
    trades = []

    # Track daily loss for circuit breaker
    current_day = None
    day_start_balance = balance
    circuit_breaker_tripped = False

    i = 0
    while i < n - 1:
        row = df.iloc[i]
        signal = row["signal"]
        timestamp = row["timestamp"]

        # Track date for daily circuit breaker reset
        day_date = pd.to_datetime(timestamp).date()
        if day_date != current_day:
            current_day = day_date
            day_start_balance = balance
            circuit_breaker_tripped = False

        # Check circuit breaker
        if (day_start_balance - balance) / day_start_balance >= daily_circuit_breaker:
            circuit_breaker_tripped = True

        if signal != 0 and not circuit_breaker_tripped:
            entry_bar_idx = i + execution_delay
            if entry_bar_idx >= n:
                break

            entry_row = df.iloc[entry_bar_idx]
            raw_entry = entry_row["open"]
            direction = int(signal)

            # Apply slippage to entry
            if direction == 1:
                entry_price = raw_entry * (1.0 + slippage)
            else:
                entry_price = raw_entry * (1.0 - slippage)

            # Determine SL & TP
            raw_sl = row["stop_loss"]
            raw_tp = row["take_profit"]
            stop_dist = abs(entry_price - raw_sl)

            if stop_dist <= 1e-8 or np.isnan(stop_dist):
                i += 1
                continue

            # Position sizing strictly based on stop distance & correlation penalty
            adjusted_risk_fraction = risk_fraction * correlation_penalty_mult
            risk_usd = balance * adjusted_risk_fraction
            position_units = risk_usd / stop_dist

            # Cap position value at max_position_equity_pct
            max_units = (balance * max_position_equity_pct) / entry_price
            position_units = min(position_units, max_units)

            position_usd = position_units * entry_price
            entry_fee = position_usd * (fee_rate / 2.0)

            # Traversal loop through subsequent candles
            exit_price = entry_price
            exit_time = entry_row["timestamp"]
            exit_reason = "TIME_EXPIRED"
            trade_hit = False

            for j in range(entry_bar_idx, min(entry_bar_idx + 100, n)):
                c_row = df.iloc[j]
                c_high = c_row["high"]
                c_low = c_row["low"]
                c_time = c_row["timestamp"]

                if direction == 1: # LONG
                    sl_hit = c_low <= raw_sl
                    tp_hit = c_high >= raw_tp

                    # Collision handling: same candle SL + TP hit -> Conservative LOSS (SL)
                    if sl_hit and tp_hit:
                        exit_price = raw_sl * (1.0 - slippage)
                        exit_time = c_time
                        exit_reason = "SL_TP_COLLISION"
                        trade_hit = True
                        break
                    elif sl_hit:
                        exit_price = raw_sl * (1.0 - slippage)
                        exit_time = c_time
                        exit_reason = "STOP_LOSS"
                        trade_hit = True
                        break
                    elif tp_hit:
                        exit_price = raw_tp * (1.0 - slippage)
                        exit_time = c_time
                        exit_reason = "TAKE_PROFIT"
                        trade_hit = True
                        break

                elif direction == -1: # SHORT
                    sl_hit = c_high >= raw_sl
                    tp_hit = c_low <= raw_tp

                    if sl_hit and tp_hit:
                        exit_price = raw_sl * (1.0 + slippage)
                        exit_time = c_time
                        exit_reason = "SL_TP_COLLISION"
                        trade_hit = True
                        break
                    elif sl_hit:
                        exit_price = raw_sl * (1.0 + slippage)
                        exit_time = c_time
                        exit_reason = "STOP_LOSS"
                        trade_hit = True
                        break
                    elif tp_hit:
                        exit_price = raw_tp * (1.0 + slippage)
                        exit_time = c_time
                        exit_reason = "TAKE_PROFIT"
                        trade_hit = True
                        break

            if not trade_hit:
                # Exit at last bar close
                last_idx = min(entry_bar_idx + 100, n - 1)
                last_row = df.iloc[last_idx]
                if direction == 1:
                    exit_price = last_row["close"] * (1.0 - slippage)
                else:
                    exit_price = last_row["close"] * (1.0 + slippage)
                exit_time = last_row["timestamp"]
                exit_reason = "TIME_EXPIRATION"

            # Compute PnL and subtract exit fee
            exit_usd = position_units * exit_price
            exit_fee = exit_usd * (fee_rate / 2.0)
            total_fee = entry_fee + exit_fee

            if direction == 1:
                gross_pnl = exit_usd - position_usd
            else:
                gross_pnl = position_usd - exit_usd

            net_pnl = gross_pnl - total_fee
            pnl_pct = net_pnl / position_usd if position_usd > 0 else 0.0
            return_r = net_pnl / (risk_usd + 1e-8)

            balance += net_pnl
            equity_curve.append(balance)

            trades.append({
                "entry_time": entry_row["timestamp"],
                "exit_time": exit_time,
                "asset": df["asset"].iloc[0] if "asset" in df.columns else "UNKNOWN",
                "timeframe": df["timeframe"].iloc[0] if "timeframe" in df.columns else "UNKNOWN",
                "direction": "LONG" if direction == 1 else "SHORT",
                "entry_price": entry_price,
                "exit_price": exit_price,
                "position_units": position_units,
                "position_usd": position_usd,
                "risk_usd": risk_usd,
                "gross_pnl": gross_pnl,
                "total_fee": total_fee,
                "net_pnl": net_pnl,
                "pnl_pct": pnl_pct,
                "return_r": return_r,
                "exit_reason": exit_reason,
                "confidence": row.get("confidence", 0.5)
            })

            # Advance index past trade exit
            i = entry_bar_idx + 10
        else:
            i += 1

    # Calculate max drawdown
    eq_arr = np.array(equity_curve)
    peak = np.maximum.accumulate(eq_arr)
    dd = (peak - eq_arr) / peak
    max_dd = float(np.max(dd)) if len(dd) > 0 else 0.0

    return {
        "trades": trades,
        "equity_curve": equity_curve,
        "final_balance": balance,
        "max_drawdown": max_dd
    }
