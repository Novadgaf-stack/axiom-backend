"""
Statistical Evaluator Module for NEXUS-7 Final Master Research
Calculates trade statistics and checks machine-readable promotion gates for ROBUST_PROFITABLE.
"""

from typing import Dict, List, Any
import numpy as np


def evaluate_trade_statistics_final(
    trades: List[Dict[str, Any]],
    total_days: float = 60.0
) -> Dict[str, Any]:
    """
    Computes comprehensive trade performance metrics.
    """
    if not trades:
        return {
            "trade_count": 0,
            "trades_per_day": 0.0,
            "daily_participation_pct": 0.0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "net_expectancy_usd": 0.0,
            "net_profit_usd": 0.0,
            "avg_win_usd": 0.0,
            "avg_loss_usd": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0
        }

    n = len(trades)
    pnls = np.array([t["net_pnl"] for t in trades], dtype=np.float64)
    wins = pnls[pnls > 0]
    losses = np.abs(pnls[pnls < 0])

    win_rate = (len(wins) / n * 100.0) if n > 0 else 0.0
    pf = float(np.sum(wins) / np.sum(losses)) if len(losses) > 0 and np.sum(losses) > 0 else (99.0 if len(wins) > 0 else 0.0)

    net_profit = float(np.sum(pnls))
    net_exp = float(np.mean(pnls)) if n > 0 else 0.0

    avg_win = float(np.mean(wins)) if len(wins) > 0 else 0.0
    avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0.0

    # Drawdown
    equity_curve = 10000.0 + np.cumsum(pnls)
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (running_max - equity_curve) / running_max
    max_dd = float(np.max(drawdowns) * 100.0) if len(drawdowns) > 0 else 0.0

    # Sharpe & Sortino
    mean_ret = np.mean(pnls)
    std_ret = np.std(pnls)
    sharpe = float((mean_ret / (std_ret + 1e-8)) * np.sqrt(365)) if std_ret > 0 else 0.0

    downside = np.std(pnls[pnls < 0]) if np.sum(pnls < 0) > 0 else 1e-8
    sortino = float((mean_ret / (downside + 1e-8)) * np.sqrt(365)) if downside > 0 else 0.0

    # Daily Participation
    dates = set(t.get("execution_timestamp", "")[:10] for t in trades)
    days_participated = len(dates)
    daily_participation_pct = (days_participated / total_days * 100.0) if total_days > 0 else 0.0
    trades_per_day = n / total_days if total_days > 0 else 0.0

    return {
        "trade_count": n,
        "trades_per_day": round(float(trades_per_day), 2),
        "daily_participation_pct": round(float(daily_participation_pct), 1),
        "win_rate_pct": round(float(win_rate), 1),
        "profit_factor": round(float(pf), 3),
        "net_expectancy_usd": round(float(net_exp), 3),
        "net_profit_usd": round(float(net_profit), 2),
        "avg_win_usd": round(float(avg_win), 2),
        "avg_loss_usd": round(float(avg_loss), 2),
        "max_drawdown_pct": round(float(max_dd), 2),
        "sharpe_ratio": round(float(sharpe), 3),
        "sortino_ratio": round(float(sortino), 3)
    }


def evaluate_promotion_gates_final(
    stats: Dict[str, Any],
    bootstrap: Dict[str, Any],
    walk_forward: Dict[str, Any],
    anti_fragility: Dict[str, Any],
    dsr: Dict[str, Any]
) -> Tuple[str, List[str]]:
    """
    Checks machine-readable promotion gates for ROBUST_PROFITABLE.
    Possible Verdicts: ROBUST_PROFITABLE, PROMISING_BUT_INSUFFICIENT_SAMPLE,
    PROFITABLE_BUT_NOT_ROBUST, FRAGILE, NO_ROBUST_EDGE_FOUND.
    """
    reasons = []

    pf = stats.get("profit_factor", 0.0)
    n_trades = stats.get("trade_count", 0)
    net_exp = stats.get("net_expectancy_usd", 0.0)

    if pf <= 1.0 or net_exp <= 0:
        reasons.append("Non-positive net expectancy or PF <= 1.0")

    if n_trades < 30:
        reasons.append("Insufficient trade sample (N < 30)")

    if bootstrap.get("pf_ci_lower", 0.0) <= 1.0:
        reasons.append("Bootstrap 95% CI lower bound <= 1.0")

    if walk_forward.get("consistency_pct", 0.0) < 75.0:
        reasons.append("Walk-forward window consistency < 75%")

    if not anti_fragility.get("is_anti_fragile", False):
        reasons.append("Failed anti-fragility top-trade/asset removal test")

    if not dsr.get("is_statistically_significant", False):
        reasons.append("Failed Deflated Sharpe Ratio (DSR) multiple-testing correction")

    if not reasons:
        return "ROBUST_PROFITABLE", ["All machine-readable promotion gates passed."]

    if pf > 1.0 and n_trades < 30:
        return "PROMISING_BUT_INSUFFICIENT_SAMPLE", reasons
    elif pf > 1.0 and ("Failed anti-fragility" in str(reasons) or "Walk-forward" in str(reasons)):
        return "PROFITABLE_BUT_NOT_ROBUST", reasons
    elif pf > 0 and n_trades > 0:
        return "FRAGILE", reasons
    else:
        return "NO_ROBUST_EDGE_FOUND", reasons
