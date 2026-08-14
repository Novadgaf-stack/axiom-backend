"""
NEXUS-7 — RESEARCH V26 STATISTICAL GATES
Computes Net Profit Factor, Net Expectancy, 1,000-iteration Bootstrap 95% CIs, friction sensitivity (0.15%, 0.30%, 0.45%),
and enforces strict out-of-sample statistical pass/fail rules.
"""
import random
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple


def compute_bootstrap_ci(trades: List[Dict[str, Any]], num_iterations: int = 1000, seed: int = 42) -> Tuple[float, float]:
    """
    Computes 1,000-iteration bootstrap 95% Confidence Interval for Profit Factor.
    Returns (lower_bound_95, upper_bound_95).
    """
    if not trades or len(trades) < 5:
        return 0.0, 0.0

    random.seed(seed)
    np.random.seed(seed)

    pfs = []
    trade_pnls = [t["net_pnl"] for t in trades]
    n = len(trade_pnls)

    for _ in range(num_iterations):
        sample = np.random.choice(trade_pnls, size=n, replace=True)
        gains = np.sum(sample[sample > 0])
        losses = np.abs(np.sum(sample[sample < 0]))
        if losses == 0:
            pf = 10.0 if gains > 0 else 1.0
        else:
            pf = gains / losses
        pfs.append(pf)

    lower_bound = float(np.percentile(pfs, 2.5))
    upper_bound = float(np.percentile(pfs, 97.5))
    return lower_bound, upper_bound


def evaluate_trade_sequence(
    trades: List[Dict[str, Any]],
    total_days: float,
    friction_pct: float = 0.0015,
    risk_per_trade_pct: float = 0.005,
    initial_equity: float = 10000.0
) -> Dict[str, Any]:
    """
    Evaluates a sequence of trades under specified friction and risk per trade.
    """
    if not trades or total_days <= 0:
        return {
            "total_trades": 0,
            "trades_per_day": 0.0,
            "win_rate": 0.0,
            "net_pf": 0.0,
            "net_expectancy_r": 0.0,
            "net_expectancy_usd": 0.0,
            "max_drawdown_pct": 0.0,
            "bootstrap_ci": (0.0, 0.0),
            "final_equity": initial_equity
        }

    equity = initial_equity
    peak_equity = initial_equity
    max_dd = 0.0

    adjusted_trades = []
    gross_gains = 0.0
    gross_losses = 0.0
    wins = 0

    for t in trades:
        raw_r = t.get("r_multiple", 0.0)
        # Apply friction (0.15%, 0.30%, 0.45% round-trip)
        net_r = raw_r - (friction_pct / risk_per_trade_pct)
        risk_usd = equity * risk_per_trade_pct
        net_pnl_usd = net_r * risk_usd

        equity += net_pnl_usd
        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity
        if dd > max_dd:
            max_dd = dd

        if net_r > 0:
            wins += 1
            gross_gains += net_pnl_usd
        else:
            gross_losses += abs(net_pnl_usd)

        adjusted_trades.append({
            "raw_r": raw_r,
            "net_r": net_r,
            "net_pnl": net_pnl_usd
        })

    n_trades = len(adjusted_trades)
    trades_per_day = n_trades / total_days
    win_rate = (wins / n_trades) * 100.0 if n_trades > 0 else 0.0

    if gross_losses == 0:
        net_pf = 10.0 if gross_gains > 0 else 1.0
    else:
        net_pf = gross_gains / gross_losses

    avg_net_r = float(np.mean([t["net_r"] for t in adjusted_trades])) if n_trades > 0 else 0.0
    avg_net_usd = float(np.mean([t["net_pnl"] for t in adjusted_trades])) if n_trades > 0 else 0.0

    ci_lower, ci_upper = compute_bootstrap_ci(adjusted_trades, num_iterations=1000)

    return {
        "total_trades": n_trades,
        "trades_per_day": round(trades_per_day, 2),
        "win_rate": round(win_rate, 2),
        "net_pf": round(net_pf, 2),
        "net_expectancy_r": round(avg_net_r, 3),
        "net_expectancy_usd": round(avg_net_usd, 2),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "bootstrap_ci": (round(ci_lower, 2), round(ci_upper, 2)),
        "final_equity": round(equity, 2)
    }


def check_statistical_gates(metrics: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates candidate metrics against V26 statistical gates:
    1. Net PF >= 1.25 (at 0.15% friction)
    2. Bootstrap 95% CI Lower Bound > 1.00
    3. Net Expectancy > 0.00R
    4. Max Drawdown <= 25.0%
    """
    net_pf = metrics.get("net_pf", 0.0)
    ci_lower = metrics.get("bootstrap_ci", (0.0, 0.0))[0]
    exp_r = metrics.get("net_expectancy_r", 0.0)
    max_dd = metrics.get("max_drawdown_pct", 100.0)

    rejections = []

    if net_pf < 1.25:
        rejections.append(f"Net PF {net_pf:.2f} < 1.25")
    if ci_lower <= 1.00:
        rejections.append(f"Bootstrap CI Lower Bound {ci_lower:.2f} <= 1.00")
    if exp_r <= 0.0:
        rejections.append(f"Net Expectancy {exp_r:.3f}R <= 0.00R")
    if max_dd > 25.0:
        rejections.append(f"Max Drawdown {max_dd:.1f}% > 25.0%")

    if not rejections:
        return True, "QUALIFIED (EDGE PROVEN)"
    else:
        return False, f"REJECTED ({'; '.join(rejections)})"
