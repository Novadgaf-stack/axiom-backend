"""
Statistical Evaluator Module for NEXUS-7 Research V38
Calculates comprehensive trade statistics, metrics, promotion gates, and official verdict assignment.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def compute_trade_statistics_v38(
    trades: List[Dict[str, Any]],
    initial_balance: float = 1000.0,
    total_days: float = 30.0
) -> Dict[str, Any]:
    """Computes trade performance statistics."""
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "net_expectancy": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "trades_per_day": 0.0
        }

    pnls = np.array([t["net_pnl"] for t in trades], dtype=float)
    wins = pnls[pnls > 0]
    losses = np.abs(pnls[pnls < 0])

    n_trades = len(trades)
    win_rate = len(wins) / n_trades if n_trades > 0 else 0.0

    gross_win = np.sum(wins) if len(wins) > 0 else 0.0
    gross_loss = np.sum(losses) if len(losses) > 0 else 0.0

    pf = gross_win / gross_loss if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
    expectancy = np.mean(pnls) if n_trades > 0 else 0.0

    std_pnl = np.std(pnls) if n_trades > 1 else 1e-6
    sharpe = (expectancy / std_pnl) * np.sqrt(252) if std_pnl > 0 else 0.0

    downside_losses = np.abs(pnls[pnls < 0])
    downside_std = np.std(downside_losses) if len(downside_losses) > 1 else 1e-6
    sortino = (expectancy / downside_std) * np.sqrt(252) if downside_std > 0 else 0.0

    cum_pnls = np.cumsum(pnls)
    equity_curve = initial_balance + cum_pnls
    peak = initial_balance
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    trades_per_day = n_trades / max(1.0, total_days)

    return {
        "total_trades": n_trades,
        "win_rate": round(win_rate * 100.0, 2),
        "profit_factor": round(float(pf), 3),
        "net_expectancy": round(float(expectancy), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "sortino_ratio": round(float(sortino), 2),
        "max_drawdown_pct": round(float(max_dd) * 100.0, 2),
        "trades_per_day": round(float(trades_per_day), 2)
    }


def evaluate_v38_promotion_gates(
    stats: Dict[str, Any],
    bootstrap_ci: List[float],
    wf_positive_windows: int,
    total_wf_windows: int = 5,
    param_stability_pct: float = 50.0,
    best_trade_removal_pf: float = 1.0,
    best_asset_removal_pf: float = 1.0,
    friction_stress_pf: float = 1.0,
    max_asset_profit_share: float = 0.25,
    mc_95_dd_pct: float = 10.0,
    dsr_passed: bool = False,
    is_fragile: bool = False
) -> Tuple[str, Dict[str, bool]]:
    """
    Evaluates strict V38 machine-readable promotion gates for ROBUST_PROFITABLE status.
    """
    pf = stats.get("profit_factor", 0.0)
    exp = stats.get("net_expectancy", 0.0)
    tpd = stats.get("trades_per_day", 0.0)
    bs_lower = bootstrap_ci[0] if len(bootstrap_ci) >= 2 else 0.0

    gates = {
        "gate_pf_min": bool(pf >= 1.15),
        "gate_exp_positive": bool(exp > 0.0),
        "gate_bootstrap_lower": bool(bs_lower > 1.00),
        "gate_walk_forward": bool(wf_positive_windows >= 4 and total_wf_windows >= 5),
        "gate_param_stability": bool(param_stability_pct >= 70.0),
        "gate_best_trade_removal": bool(best_trade_removal_pf >= 1.0),
        "gate_best_asset_removal": bool(best_asset_removal_pf >= 1.0),
        "gate_friction_stress": bool(friction_stress_pf >= 1.0),
        "gate_concentration": bool(max_asset_profit_share <= 0.30),
        "gate_mc_drawdown": bool(mc_95_dd_pct <= 25.0),
        "gate_frequency": bool(tpd >= 0.75),
        "gate_not_fragile": bool(not is_fragile)
    }

    all_passed = all(gates.values())

    if is_fragile:
        verdict = "FRAGILE"
    elif all_passed:
        if tpd >= 3.0:
            verdict = "ROBUST_HIGH_FREQUENCY"
        elif tpd >= 0.75:
            verdict = "ROBUST_DAILY"
        else:
            verdict = "ROBUST_LOW_FREQUENCY"
    elif pf > 1.0 and exp > 0.0:
        verdict = "V38_PROFITABLE_BUT_NOT_ROBUST"
    elif tpd >= 0.75 and (pf <= 1.0 or exp <= 0.0):
        verdict = "V38_FREQUENT_BUT_UNPROFITABLE"
    elif stats.get("total_trades", 0) < 10:
        verdict = "V38_INSUFFICIENT_SAMPLE"
    else:
        verdict = "NO_ROBUST_EDGE_FOUND"

    return verdict, gates
