"""
Portfolio Constructor & Risk Control Module for NEXUS-7 Research V35
Enforces cross-asset correlation control (0.60, 0.70, 0.80, 0.90 thresholds) and portfolio risk caps.
Prevents multiple correlated signals from forming an unmanaged market cluster bet.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def construct_correlated_portfolio(
    ranked_signals: List[Dict[str, Any]],
    corr_matrix: pd.DataFrame,
    max_aggregate_risk: float = 0.015,       # 1.50% max open risk
    max_correlated_risk: float = 0.010,      # 1.00% max correlated risk
    max_simultaneous_positions: int = 5,    # 5 max positions
    corr_threshold: float = 0.70
) -> List[Dict[str, Any]]:
    """
    Constructs risk-managed portfolio by filtering out correlated excess risk above threshold.
    """
    if not ranked_signals:
        return []

    accepted = []
    accepted_assets = []
    current_open_risk = 0.0
    current_correlated_risk = 0.0

    for sig in ranked_signals:
        if len(accepted) >= max_simultaneous_positions:
            break

        asset = sig.get("asset", "BTC")
        risk_pct = sig.get("risk_pct", 0.005)

        if current_open_risk + risk_pct > max_aggregate_risk:
            continue  # Aggregate open risk cap reached

        is_correlated = False
        for acc in accepted_assets:
            if asset in corr_matrix.columns and acc in corr_matrix.columns:
                c_val = abs(corr_matrix.loc[asset, acc])
                if c_val >= corr_threshold:
                    is_correlated = True
                    break

        if is_correlated:
            if current_correlated_risk + risk_pct > max_correlated_risk:
                continue # Correlated exposure limit reached
            sig["correlation_penalty_mult"] = 0.70
            current_correlated_risk += risk_pct * 0.70
        else:
            sig["correlation_penalty_mult"] = 1.00

        accepted.append(sig)
        accepted_assets.append(asset)
        current_open_risk += risk_pct * sig["correlation_penalty_mult"]

    return accepted
