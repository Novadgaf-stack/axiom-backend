"""
Statistical Evaluator Module for NEXUS-7 Research V35
Computes trade statistics, Bootstrap 95% CIs, Sharpe, Sortino, asset concentration,
evaluates promotion gates, and assigns official research verdicts.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def compute_trade_statistics(
    trades: List[Dict[str, Any]],
    initial_balance: float = 1000.0,
    total_days: float = 90.0,
    bootstrap_iterations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """Computes comprehensive trade statistics, metrics, and bootstrap CIs."""
    if not trades:
        return {
            "total_trades": 0,
            "trades_per_day": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "expectancy_trade": 0.0,
            "expectancy_r": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "longest_losing_streak": 0,
            "net_profit": 0.0,
            "final_balance": initial_balance,
            "asset_concentration_pct": 0.0,
            "passed_bootstrap_gate": False
        }

    df_tr = pd.DataFrame(trades)
    pnls = df_tr["net_pnl"].values
    pnls_r = df_tr["pnl_r"].values

    total_trades = len(trades)
    trades_per_day = total_trades / max(1.0, total_days)

    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]

    win_rate = len(wins) / total_trades if total_trades > 0 else 0.0

    gross_profit = float(np.sum(wins)) if len(wins) > 0 else 0.0
    gross_loss = float(np.abs(np.sum(losses))) if len(losses) > 0 else 0.0

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = 99.0 if gross_profit > 0 else 0.0

    expectancy_trade = float(np.mean(pnls))
    expectancy_r = float(np.mean(pnls_r))

    rng = np.random.default_rng(seed)
    boot_pfs = []
    for _ in range(bootstrap_iterations):
        sample_pnls = rng.choice(pnls, size=total_trades, replace=True)
        w = sample_pnls[sample_pnls > 0]
        l = sample_pnls[sample_pnls < 0]
        gp = np.sum(w) if len(w) > 0 else 0.0
        gl = np.abs(np.sum(l)) if len(l) > 0 else 0.0
        pf = gp / gl if gl > 0 else (99.0 if gp > 0 else 0.0)
        boot_pfs.append(pf)

    ci_lower = float(np.percentile(boot_pfs, 2.5))
    ci_upper = float(np.percentile(boot_pfs, 97.5))

    cum_pnls = np.cumsum(pnls)
    equity_curve = initial_balance + np.insert(cum_pnls, 0, 0.0)
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    daily_returns = pd.Series(pnls).groupby(np.arange(len(pnls)) // 4).sum() / initial_balance
    mean_ret = daily_returns.mean()
    std_ret = daily_returns.std()
    sharpe_ratio = float((mean_ret / (std_ret + 1e-8)) * np.sqrt(365)) if std_ret > 0 else 0.0

    downside_std = daily_returns[daily_returns < 0].std()
    sortino_ratio = float((mean_ret / (downside_std + 1e-8)) * np.sqrt(365)) if downside_std > 0 else 0.0

    longest_losing_streak = 0
    current_streak = 0
    for p in pnls:
        if p < 0:
            current_streak += 1
            if current_streak > longest_losing_streak:
                longest_losing_streak = current_streak
        else:
            current_streak = 0

    asset_pnls = df_tr.groupby("asset")["net_pnl"].sum()
    top_asset_pnl = float(asset_pnls.max()) if len(asset_pnls) > 0 else 0.0
    tot_pnl = float(np.sum(pnls))
    asset_concentration_pct = (top_asset_pnl / tot_pnl * 100.0) if tot_pnl > 0 else 0.0

    net_profit = float(np.sum(pnls))
    final_balance = initial_balance + net_profit
    passed_bootstrap_gate = bool(ci_lower > 1.00 and profit_factor >= 1.25)

    return {
        "total_trades": total_trades,
        "trades_per_day": round(trades_per_day, 2),
        "win_rate": round(win_rate * 100, 1),
        "profit_factor": round(profit_factor, 3),
        "expectancy_trade": round(expectancy_trade, 2),
        "expectancy_r": round(expectancy_r, 3),
        "ci_lower": round(ci_lower, 3),
        "ci_upper": round(ci_upper, 3),
        "max_drawdown": round(max_dd * 100, 1),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sortino_ratio": round(sortino_ratio, 2),
        "longest_losing_streak": longest_losing_streak,
        "net_profit": round(net_profit, 2),
        "final_balance": round(final_balance, 2),
        "asset_concentration_pct": round(asset_concentration_pct, 1),
        "passed_bootstrap_gate": passed_bootstrap_gate
    }


def assign_official_verdict(
    stats: Dict[str, Any],
    wf_positive_windows: int = 0,
    wf_total_windows: int = 5,
    is_stable: bool = False,
    in_target_frequency_window: bool = False
) -> str:
    """
    Evaluates promotion gates and assigns official V35 verdict:
    - V35_ROBUST_PROFITABLE_EDGE_FOUND
    - V35_PROFITABLE_BUT_NOT_ROBUST
    - V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE
    - V35_NO_ROBUST_PROFITABLE_EDGE
    - V35_INVALIDATED
    """
    total_trades = stats.get("total_trades", 0)
    pf = stats.get("profit_factor", 0.0)
    net_exp = stats.get("expectancy_trade", 0.0)
    ci_lower = stats.get("ci_lower", 0.0)
    max_dd = stats.get("max_drawdown", 0.0) / 100.0
    asset_conc = stats.get("asset_concentration_pct", 0.0)

    if total_trades < 30:
        return "V35_NO_ROBUST_PROFITABLE_EDGE"

    wf_pct = wf_positive_windows / max(1, wf_total_windows)

    if (
        pf >= 1.25 and
        net_exp > 0 and
        ci_lower > 1.00 and
        wf_pct >= 0.60 and
        is_stable and
        max_dd <= 0.15 and
        asset_conc <= 60.0
    ):
        return "V35_ROBUST_PROFITABLE_EDGE_FOUND"

    if pf > 1.00 and net_exp > 0:
        return "V35_PROFITABLE_BUT_NOT_ROBUST"

    if stats.get("trades_per_day", 0.0) >= 0.75 and pf <= 1.00:
        return "V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE"

    return "V35_NO_ROBUST_PROFITABLE_EDGE"
