"""
Asset Replication & Cross-Sectional Analysis Module for NEXUS-7 Research V39
Evaluates cross-asset replication metrics:
BTC contribution, ETH contribution, SOL contribution, top-asset share,
median asset expectancy, percentage of profitable assets, and cross-sectional expectancy.
Generates V39_ASSET_REPLICATION.csv.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def analyze_cross_asset_replication_v39(
    trades: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyzes whether strategy edge replicates across multiple independent assets.
    """
    if not trades:
        return {
            "btc_profit_share": 0.0,
            "eth_profit_share": 0.0,
            "sol_profit_share": 0.0,
            "top_asset_share": 0.0,
            "median_asset_expectancy": 0.0,
            "pct_profitable_assets": 0.0,
            "cross_sectional_expectancy": 0.0,
            "asset_replication_passed": False
        }

    total_net_profit = sum(t["net_pnl"] for t in trades)

    asset_pnls = {}
    asset_trades = {}
    for t in trades:
        a = t["asset"]
        asset_pnls[a] = asset_pnls.get(a, 0.0) + t["net_pnl"]
        asset_trades[a] = asset_trades.get(a, 0) + 1

    btc_pnl = asset_pnls.get("BTC", 0.0)
    eth_pnl = asset_pnls.get("ETH", 0.0)
    sol_pnl = asset_pnls.get("SOL", 0.0)

    btc_share = (btc_pnl / total_net_profit) if total_net_profit > 0 else 0.0
    eth_share = (eth_pnl / total_net_profit) if total_net_profit > 0 else 0.0
    sol_share = (sol_pnl / total_net_profit) if total_net_profit > 0 else 0.0

    sorted_assets = sorted(asset_pnls.items(), key=lambda x: x[1], reverse=True)
    top_asset_pnl = sorted_assets[0][1] if sorted_assets else 0.0
    top_asset_share = (top_asset_pnl / total_net_profit) if total_net_profit > 0 else 0.0

    expectancies = [asset_pnls[a] / max(1, asset_trades[a]) for a in asset_pnls]
    median_exp = float(np.median(expectancies)) if expectancies else 0.0
    mean_exp = float(np.mean(expectancies)) if expectancies else 0.0

    profitable_count = sum(1 for p in asset_pnls.values() if p > 0)
    pct_profitable = (profitable_count / max(1, len(asset_pnls))) * 100.0

    replication_passed = bool(pct_profitable >= 50.0 and top_asset_share <= 0.35)

    return {
        "btc_profit_share": round(btc_share * 100.0, 1),
        "eth_profit_share": round(eth_share * 100.0, 1),
        "sol_profit_share": round(sol_share * 100.0, 1),
        "top_asset_share": round(top_asset_share * 100.0, 1),
        "median_asset_expectancy": round(median_exp, 2),
        "pct_profitable_assets": round(pct_profitable, 1),
        "cross_sectional_expectancy": round(mean_exp, 2),
        "asset_replication_passed": replication_passed
    }
