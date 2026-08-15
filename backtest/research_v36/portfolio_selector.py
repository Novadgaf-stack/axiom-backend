"""
Portfolio Selector & Risk Control Module for NEXUS-7 Research V36
Enforces cross-asset correlation control (0.60, 0.70, 0.80, 0.90 thresholds),
simultaneous position limits (1, 2, 3, 5, 8), aggregate open risk caps (1.0%–2.5%),
correlated risk caps (0.5%–1.5%), asset & strategy family concentration limits.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def construct_correlated_portfolio(
    ranked_opportunities: List[Dict[str, Any]],
    corr_matrix: pd.DataFrame,
    max_aggregate_risk: float = 0.015,       # 1.50% max open risk
    max_correlated_risk: float = 0.010,      # 1.00% max correlated risk
    max_simultaneous_positions: int = 5,    # 5 max positions
    corr_threshold: float = 0.70,
    max_asset_concentration: int = 2,
    max_family_concentration: int = 3
) -> List[Dict[str, Any]]:
    """
    Constructs risk-managed portfolio by filtering out correlated excess risk above threshold.
    """
    if not ranked_opportunities:
        return []

    accepted = []
    accepted_assets = []
    asset_counts = {}
    family_counts = {}
    current_open_risk = 0.0
    current_correlated_risk = 0.0

    for opp in ranked_opportunities:
        if len(accepted) >= max_simultaneous_positions:
            break

        asset = opp.get("asset", "BTC")
        family = opp.get("strategy_family", "momentum_cont")
        risk_pct = opp.get("risk_pct", 0.005)

        if asset_counts.get(asset, 0) >= max_asset_concentration:
            continue

        if family_counts.get(family, 0) >= max_family_concentration:
            continue

        if current_open_risk + risk_pct > max_aggregate_risk:
            continue

        is_correlated = False
        for acc in accepted_assets:
            if asset in corr_matrix.columns and acc in corr_matrix.columns:
                c_val = abs(corr_matrix.loc[asset, acc])
                if c_val >= corr_threshold:
                    is_correlated = True
                    break

        if is_correlated:
            if current_correlated_risk + risk_pct > max_correlated_risk:
                continue
            opp["correlation_penalty_mult"] = 0.70
            current_correlated_risk += risk_pct * 0.70
        else:
            opp["correlation_penalty_mult"] = 1.00

        accepted.append(opp)
        accepted_assets.append(asset)
        asset_counts[asset] = asset_counts.get(asset, 0) + 1
        family_counts[family] = family_counts.get(family, 0) + 1
        current_open_risk += risk_pct * opp["correlation_penalty_mult"]

    return accepted
