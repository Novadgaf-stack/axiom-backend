"""
NEXUS-7 Research V31 — Statistical Evaluator Module
Computes true Profit Factor, Win Rate, Net Expectancy ($ & R), Max Drawdown, Trades/Day,
1,000-iteration Bootstrap 95% CIs, economic significance metrics, sample size checks,
and maps candidates to official verdict categories.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd


def compute_trade_statistics(
    trades: List[Dict[str, Any]],
    total_days: float = 90.0,
    initial_balance: float = 1000.0,
    bootstrap_iterations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """Computes comprehensive performance, economic significance metrics, and bootstrap 95% CI."""
    if not trades:
        return {
            "total_trades": 0,
            "trades_per_day": 0.0,
            "win_rate": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "net_pnl": 0.0,
            "profit_factor": 0.0,
            "expectancy_trade": 0.0,
            "expectancy_r": 0.0,
            "max_drawdown": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "fees_paid": 0.0,
            "longest_losing_streak": 0,
            "sample_status": "INSUFFICIENT SAMPLE (<100 trades)",
            "verdict": "NO_ROBUST_PROFITABLE_EDGE_FOUND"
        }

    pnls = np.array([t["net_pnl"] for t in trades])
    returns_r = np.array([t["return_r"] for t in trades])
    fees = np.array([t["total_fee"] for t in trades])

    total_trades = len(pnls)
    trades_per_day = total_trades / max(total_days, 1.0)

    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]

    win_rate = float(len(wins) / total_trades) if total_trades > 0 else 0.0
    gross_profit = float(np.sum(wins)) if len(wins) > 0 else 0.0
    gross_loss = float(np.abs(np.sum(losses))) if len(losses) > 0 else 0.0

    if gross_loss > 1e-8:
        profit_factor = float(gross_profit / gross_loss)
    elif gross_profit > 1e-8:
        profit_factor = 99.0
    else:
        profit_factor = 0.0

    net_pnl = float(np.sum(pnls))
    expectancy_trade = float(np.mean(pnls)) if total_trades > 0 else 0.0
    expectancy_r = float(np.mean(returns_r)) if total_trades > 0 else 0.0
    total_fees_paid = float(np.sum(fees))

    # Longest losing streak
    max_streak = 0
    current_streak = 0
    for p in pnls:
        if p < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    # Drawdown from equity curve
    equity_curve = [initial_balance]
    b = initial_balance
    for p in pnls:
        b += p
        equity_curve.append(b)

    eq_arr = np.array(equity_curve)
    peak = np.maximum.accumulate(eq_arr)
    dd = (peak - eq_arr) / peak
    max_drawdown = float(np.max(dd)) if len(dd) > 0 else 0.0

    # 1,000-iteration Bootstrap 95% Confidence Interval for Profit Factor
    rng = np.random.default_rng(seed)
    bootstrap_pfs = []

    for _ in range(bootstrap_iterations):
        sample_pnls = rng.choice(pnls, size=total_trades, replace=True)
        s_wins = np.sum(sample_pnls[sample_pnls > 0])
        s_losses = np.abs(np.sum(sample_pnls[sample_pnls < 0]))
        if s_losses > 1e-8:
            pf = s_wins / s_losses
        elif s_wins > 1e-8:
            pf = 10.0
        else:
            pf = 0.0
        bootstrap_pfs.append(pf)

    ci_lower = float(np.percentile(bootstrap_pfs, 2.5))
    ci_upper = float(np.percentile(bootstrap_pfs, 97.5))

    sample_sufficient = total_trades >= 100
    sample_status = "SUFFICIENT SAMPLE (>=100 trades)" if sample_sufficient else "INSUFFICIENT SAMPLE (<100 trades)"

    # Official Verdict Determination
    in_target_freq = 0.8 <= trades_per_day <= 1.5
    gate_pf = profit_factor >= 1.25
    gate_ci = ci_lower > 1.00
    gate_exp = expectancy_trade > 0.0
    gate_dd = max_drawdown <= 0.15

    if not sample_sufficient and gate_pf and gate_exp:
        verdict = "PROMISING_BUT_INSUFFICIENT_SAMPLE"
    elif in_target_freq and not gate_exp:
        verdict = "FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE"
    elif gate_exp and profit_factor > 1.0 and (not gate_ci or not gate_pf or not gate_dd):
        verdict = "PROFITABLE_BUT_NOT_ROBUST"
    elif sample_sufficient and in_target_freq and gate_pf and gate_ci and gate_exp and gate_dd:
        verdict = "ROBUST_EDGE_FOUND"
    else:
        verdict = "NO_ROBUST_PROFITABLE_EDGE_FOUND"

    return {
        "total_trades": total_trades,
        "trades_per_day": trades_per_day,
        "win_rate": win_rate,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net_pnl": net_pnl,
        "profit_factor": profit_factor,
        "expectancy_trade": expectancy_trade,
        "expectancy_r": expectancy_r,
        "max_drawdown": max_drawdown,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "fees_paid": total_fees_paid,
        "longest_losing_streak": max_streak,
        "sample_status": sample_status,
        "verdict": verdict
    }
