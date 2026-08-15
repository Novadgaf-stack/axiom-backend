"""
Asset Replication Module for NEXUS-7 Final Master Research
Evaluates strategy performance replication across individual liquid assets.
Reports BTC/ETH/SOL contributions, top-asset share, median asset expectancy,
median asset PF, and % of assets profitable.
"""

from typing import Dict, List, Any
import numpy as np


def evaluate_asset_replication_final(
    trades: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes cross-asset replication metrics.
    """
    if not trades:
        return {
            "total_assets_traded": 0,
            "profitable_assets_count": 0,
            "pct_assets_profitable": 0.0,
            "top_asset_profit_share": 0.0,
            "btc_eth_sol_profit_share": 0.0,
            "median_asset_expectancy": 0.0,
            "median_asset_pf": 0.0,
            "asset_details": {}
        }

    asset_trades = {}
    total_net_pnl = sum(t["net_pnl"] for t in trades)

    for t in trades:
        a = t["asset"]
        if a not in asset_trades:
            asset_trades[a] = []
        asset_trades[a].append(t)

    asset_metrics = {}
    profitable_count = 0
    asset_pfs = []
    asset_expectancies = []

    for a, a_list in asset_trades.items():
        pnls = [t["net_pnl"] for t in a_list]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        net_profit = sum(pnls)
        exp = net_profit / len(a_list)

        if net_profit > 0 and pf > 1.0:
            profitable_count += 1

        asset_pfs.append(pf)
        asset_expectancies.append(exp)

        asset_metrics[a] = {
            "trade_count": len(a_list),
            "net_profit": round(net_profit, 2),
            "profit_factor": round(pf, 3),
            "expectancy": round(exp, 3),
            "win_rate_pct": round(len(wins) / len(a_list) * 100.0, 1)
        }

    n_traded = len(asset_trades)
    pct_profitable = (profitable_count / n_traded * 100.0) if n_traded > 0 else 0.0

    sorted_pnl = sorted([m["net_profit"] for m in asset_metrics.values()], reverse=True)
    top_asset_share = (sorted_pnl[0] / total_net_pnl) if sorted_pnl and total_net_pnl > 0 else 0.0

    btc_eth_sol_pnl = sum(asset_metrics.get(a, {}).get("net_profit", 0.0) for a in ["BTC", "ETH", "SOL"])
    btc_eth_sol_share = (btc_eth_sol_pnl / total_net_pnl) if total_net_pnl > 0 else 0.0

    return {
        "total_assets_traded": n_traded,
        "profitable_assets_count": profitable_count,
        "pct_assets_profitable": round(pct_profitable, 1),
        "top_asset_profit_share": round(top_asset_share, 3),
        "btc_eth_sol_profit_share": round(btc_eth_sol_share, 3),
        "median_asset_expectancy": round(float(np.median(asset_expectancies)), 3) if asset_expectancies else 0.0,
        "median_asset_pf": round(float(np.median(asset_pfs)), 3) if asset_pfs else 0.0,
        "asset_details": asset_metrics
    }
