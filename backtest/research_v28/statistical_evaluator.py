"""
NEXUS-7 — RESEARCH V28 STATISTICAL EVALUATOR
Computes true out-of-sample performance metrics, 1,000-iteration bootstrap 95% CIs,
statistical gates, and parameter sensitivity testing (±10% threshold adjustments).
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple


def evaluate_trade_ledger(trade_ledger: List[Dict[str, Any]], total_days: float) -> Dict[str, Any]:
    """Computes summary metrics for a sequence of candle-resolved trades."""
    if not trade_ledger or total_days <= 0:
        return {
            "total_trades": 0,
            "trades_per_day": 0.0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate_pct": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "total_net_pnl": 0.0,
            "net_pnls": []
        }

    net_pnls = [t["net_pnl"] for t in trade_ledger]
    total_trades = len(net_pnls)
    trades_per_day = total_trades / total_days

    winning_trades = [p for p in net_pnls if p > 0]
    losing_trades = [p for p in net_pnls if p <= 0]

    win_count = len(winning_trades)
    loss_count = len(losing_trades)
    win_rate_pct = (win_count / total_trades) * 100.0 if total_trades > 0 else 0.0

    gross_profit = float(sum(winning_trades)) if winning_trades else 0.0
    gross_loss = float(abs(sum(losing_trades))) if losing_trades else 0.0

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = 99.0 if gross_profit > 0 else 0.0

    # Drawdown from equity curve
    dds = [t["drawdown_pct"] for t in trade_ledger]
    max_drawdown_pct = float(np.max(dds)) if dds else 0.0

    total_net_pnl = float(sum(net_pnls))

    return {
        "total_trades": total_trades,
        "trades_per_day": round(trades_per_day, 2),
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate_pct": round(win_rate_pct, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "total_net_pnl": round(total_net_pnl, 2),
        "net_pnls": net_pnls
    }


def compute_bootstrap_pnl_ci(net_pnls: List[float], num_iterations: int = 1000, seed: int = 42) -> Tuple[float, float, float]:
    """
    Computes 1,000-iteration bootstrap 95% Confidence Interval on actual trade PnLs / Profit Factors.
    Returns: (pf_mean, pf_lower_95, pf_upper_95).
    """
    if not net_pnls or len(net_pnls) < 5:
        return 0.0, 0.0, 0.0

    rng = np.random.RandomState(seed)
    n = len(net_pnls)
    arr = np.array(net_pnls)

    bootstrap_pfs = []
    for _ in range(num_iterations):
        sample = rng.choice(arr, size=n, replace=True)
        wins = sample[sample > 0]
        losses = sample[sample <= 0]

        sum_w = np.sum(wins) if len(wins) > 0 else 0.0
        sum_l = np.abs(np.sum(losses)) if len(losses) > 0 else 0.0

        b_pf = sum_w / sum_l if sum_l > 0 else (99.0 if sum_w > 0 else 0.0)
        bootstrap_pfs.append(b_pf)

    mean_val = float(np.mean(bootstrap_pfs))
    lower_bound = float(np.percentile(bootstrap_pfs, 2.5))
    upper_bound = float(np.percentile(bootstrap_pfs, 97.5))

    return round(mean_val, 2), round(lower_bound, 2), round(upper_bound, 2)


def check_v28_statistical_gates(metrics: Dict[str, Any], bootstrap_ci: Tuple[float, float, float]) -> Dict[str, Any]:
    """
    Checks V28 statistical promotion gates:
    1. Trades Per Day: 0.8 to 1.8 (~1-1.5/day target).
    2. Profit Factor >= 1.25.
    3. Bootstrap 95% PF CI Lower Bound > 1.00.
    4. Max Drawdown <= 15.0%.
    5. Minimum Trades >= 20.
    """
    tpd = metrics["trades_per_day"]
    pf = metrics["profit_factor"]
    max_dd = metrics["max_drawdown_pct"]
    total_trades = metrics["total_trades"]
    ci_mean, ci_lower, ci_upper = bootstrap_ci

    tpd_pass = 0.8 <= tpd <= 1.8
    pf_pass = pf >= 1.25
    ci_pass = ci_lower > 1.00
    dd_pass = max_dd <= 15.0
    trades_pass = total_trades >= 20

    overall_pass = tpd_pass and pf_pass and ci_pass and dd_pass and trades_pass

    rejection_reasons = []
    if not tpd_pass:
        rejection_reasons.append(f"Trades/Day ({tpd}) outside target window [0.8, 1.8]")
    if not pf_pass:
        rejection_reasons.append(f"Profit Factor ({pf}) < 1.25 target")
    if not ci_pass:
        rejection_reasons.append(f"Bootstrap 95% PF CI lower bound ({ci_lower}) <= 1.00")
    if not dd_pass:
        rejection_reasons.append(f"Max Drawdown ({max_dd}%) > 15.0% limit")
    if not trades_pass:
        rejection_reasons.append(f"Total Trades ({total_trades}) < 20 minimum")

    return {
        "overall_pass": overall_pass,
        "tpd_pass": tpd_pass,
        "pf_pass": pf_pass,
        "ci_pass": ci_pass,
        "dd_pass": dd_pass,
        "trades_pass": trades_pass,
        "rejection_reasons": rejection_reasons,
        "verdict": "PASSED" if overall_pass else "REJECTED (NO EDGE PROVEN)"
    }
