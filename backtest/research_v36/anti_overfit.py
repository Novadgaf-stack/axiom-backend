"""
Anti-Overfit & Adversarial Removal Module for NEXUS-7 Research V36
Executes adversarial removal tests:
1. Remove best 1%, 5%, 10% of trades
2. Remove best 1, 3, 5, 10% of assets
3. Remove best 1%, 5%, 10% of trading days
Flags fragile edge if profitability collapses immediately.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v36.statistical_evaluator import compute_trade_statistics


def run_anti_overfit_removal_tests(
    trades: List[Dict[str, Any]],
    total_days: float = 90.0
) -> Dict[str, Any]:
    """
    Executes adversarial best-trade, best-asset, and best-day removal tests.
    """
    if not trades:
        return {
            "remove_best_trades": {},
            "remove_best_assets": {},
            "remove_best_days": {},
            "has_fragile_trade_edge": False,
            "has_asset_concentration_risk": False,
            "has_day_concentration_risk": False
        }

    df_tr = pd.DataFrame(trades)
    n = len(df_tr)

    # 1. Remove Best Trades (1%, 5%, 10%)
    sorted_by_pnl = df_tr.sort_values("net_pnl", ascending=False)
    tr_rem_1 = sorted_by_pnl.iloc[max(1, int(n * 0.01)):].to_dict("records")
    tr_rem_5 = sorted_by_pnl.iloc[max(1, int(n * 0.05)):].to_dict("records")
    tr_rem_10 = sorted_by_pnl.iloc[max(1, int(n * 0.10)):].to_dict("records")

    st_rem_tr_1 = compute_trade_statistics(tr_rem_1, total_days=total_days)
    st_rem_tr_5 = compute_trade_statistics(tr_rem_5, total_days=total_days)
    st_rem_tr_10 = compute_trade_statistics(tr_rem_10, total_days=total_days)

    # 2. Remove Best Assets (Top 1, 3, 5 assets)
    asset_pnls = df_tr.groupby("asset")["net_pnl"].sum().sort_values(ascending=False)
    top_assets_1 = list(asset_pnls.index[:1])
    top_assets_3 = list(asset_pnls.index[:3])
    top_assets_5 = list(asset_pnls.index[:5])

    tr_rem_ass_1 = df_tr[~df_tr["asset"].isin(top_assets_1)].to_dict("records")
    tr_rem_ass_3 = df_tr[~df_tr["asset"].isin(top_assets_3)].to_dict("records")
    tr_rem_ass_5 = df_tr[~df_tr["asset"].isin(top_assets_5)].to_dict("records")

    st_rem_ass_1 = compute_trade_statistics(tr_rem_ass_1, total_days=total_days)
    st_rem_ass_3 = compute_trade_statistics(tr_rem_ass_3, total_days=total_days)
    st_rem_ass_5 = compute_trade_statistics(tr_rem_ass_5, total_days=total_days)

    # 3. Remove Best Days (Top 1%, 5%, 10% of trading days)
    df_tr["date"] = pd.to_datetime(df_tr["entry_time"]).dt.date
    day_pnls = df_tr.groupby("date")["net_pnl"].sum().sort_values(ascending=False)
    n_days = len(day_pnls)

    top_days_1 = list(day_pnls.index[:max(1, int(n_days * 0.01))])
    top_days_5 = list(day_pnls.index[:max(1, int(n_days * 0.05))])
    top_days_10 = list(day_pnls.index[:max(1, int(n_days * 0.10))])

    tr_rem_day_1 = df_tr[~df_tr["date"].isin(top_days_1)].to_dict("records")
    tr_rem_day_5 = df_tr[~df_tr["date"].isin(top_days_5)].to_dict("records")
    tr_rem_day_10 = df_tr[~df_tr["date"].isin(top_days_10)].to_dict("records")

    st_rem_day_1 = compute_trade_statistics(tr_rem_day_1, total_days=total_days)
    st_rem_day_5 = compute_trade_statistics(tr_rem_day_5, total_days=total_days)
    st_rem_day_10 = compute_trade_statistics(tr_rem_day_10, total_days=total_days)

    has_fragile_trade_edge = bool(st_rem_tr_5["profit_factor"] < 1.00)
    has_asset_risk = bool(st_rem_ass_1["profit_factor"] < 1.00)
    has_day_risk = bool(st_rem_day_5["profit_factor"] < 1.00)

    return {
        "remove_best_trades": {
            "rem_1pct": st_rem_tr_1,
            "rem_5pct": st_rem_tr_5,
            "rem_10pct": st_rem_tr_10
        },
        "remove_best_assets": {
            "rem_1asset": st_rem_ass_1,
            "rem_3assets": st_rem_ass_3,
            "rem_5assets": st_rem_ass_5
        },
        "remove_best_days": {
            "rem_1pct": st_rem_day_1,
            "rem_5pct": st_rem_day_5,
            "rem_10pct": st_rem_day_10
        },
        "has_fragile_trade_edge": has_fragile_trade_edge,
        "has_asset_concentration_risk": has_asset_risk,
        "has_day_concentration_risk": has_day_risk
    }
