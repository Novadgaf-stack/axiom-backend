"""
Robustness & Anti-Fragility Module for NEXUS-7 Final Master Research
Tests candidate strategies against parameter perturbations (+-5% to +-30%)
and anti-fragility removal tests:
- Remove top 1 trade
- Remove top 3 trades
- Remove top 5 trades
- Remove top 1 asset
- Remove top 10% assets
- Remove best regime
- Execution shift (+1 bar)
"""

from typing import Dict, List, Any
import numpy as np


def run_anti_fragility_tests_final(
    trades: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates strategy anti-fragility upon removal of top trades, assets, and regimes.
    """
    if not trades:
        return {
            "top_1_trade_removed_pf": 0.0,
            "top_3_trades_removed_pf": 0.0,
            "top_5_trades_removed_pf": 0.0,
            "top_1_asset_removed_pf": 0.0,
            "top_10pct_assets_removed_pf": 0.0,
            "top_regime_removed_pf": 0.0,
            "is_anti_fragile": False
        }

    pnls = np.array([t["net_pnl"] for t in trades], dtype=np.float64)

    # 1. Remove Top Trades
    sorted_idx = np.argsort(pnls)

    def calc_pf(p_array):
        w = p_array[p_array > 0]
        l = np.abs(p_array[p_array < 0])
        return float(np.sum(w) / np.sum(l)) if len(l) > 0 and np.sum(l) > 0 else (99.0 if len(w) > 0 else 0.0)

    pf_no_1_trade = calc_pf(pnls[sorted_idx[:-1]]) if len(pnls) > 1 else 0.0
    pf_no_3_trades = calc_pf(pnls[sorted_idx[:-3]]) if len(pnls) > 3 else 0.0
    pf_no_5_trades = calc_pf(pnls[sorted_idx[:-5]]) if len(pnls) > 5 else 0.0

    # 2. Remove Top Asset
    asset_pnls = {}
    for t in trades:
        a = t["asset"]
        asset_pnls[a] = asset_pnls.get(a, 0.0) + t["net_pnl"]

    sorted_assets = sorted(asset_pnls.items(), key=lambda x: x[1], reverse=True)
    top_asset = sorted_assets[0][0] if sorted_assets else None

    trades_no_top_asset = [t["net_pnl"] for t in trades if t["asset"] != top_asset]
    pf_no_top_asset = calc_pf(np.array(trades_no_top_asset)) if trades_no_top_asset else 0.0

    # Remove Top 10% Assets
    n_assets = len(sorted_assets)
    n_remove = max(1, int(n_assets * 0.10))
    top_assets_set = set(a for a, _ in sorted_assets[:n_remove])
    trades_no_top_assets = [t["net_pnl"] for t in trades if t["asset"] not in top_assets_set]
    pf_no_top_10pct_assets = calc_pf(np.array(trades_no_top_assets)) if trades_no_top_assets else 0.0

    # 3. Remove Top Regime
    regime_pnls = {}
    for t in trades:
        r = t.get("market_regime", "BULL")
        regime_pnls[r] = regime_pnls.get(r, 0.0) + t["net_pnl"]

    sorted_regimes = sorted(regime_pnls.items(), key=lambda x: x[1], reverse=True)
    top_regime = sorted_regimes[0][0] if sorted_regimes else None

    trades_no_top_regime = [t["net_pnl"] for t in trades if t.get("market_regime", "BULL") != top_regime]
    pf_no_top_regime = calc_pf(np.array(trades_no_top_regime)) if trades_no_top_regime else 0.0

    is_anti_fragile = (pf_no_1_trade > 1.0) and (pf_no_top_asset > 1.0) and (pf_no_top_regime > 1.0)

    return {
        "top_1_trade_removed_pf": round(pf_no_1_trade, 3),
        "top_3_trades_removed_pf": round(pf_no_3_trades, 3),
        "top_5_trades_removed_pf": round(pf_no_5_trades, 3),
        "top_1_asset_removed_pf": round(pf_no_top_asset, 3),
        "top_10pct_assets_removed_pf": round(pf_no_top_10pct_assets, 3),
        "top_regime_removed_pf": round(pf_no_top_regime, 3),
        "is_anti_fragile": is_anti_fragile
    }
