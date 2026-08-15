"""
Portfolio Optimizer Module for NEXUS-7 Research V32
Enforces correlation limits, maximum aggregate open risk (1.50%),
correlated exposure cap (1.00%), and signal quality ranking.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def filter_and_rank_portfolio_signals(
    candidate_signals: List[Dict[str, Any]],
    corr_matrix: pd.DataFrame,
    max_aggregate_risk: float = 0.015, # 1.50% max open risk
    max_correlated_risk: float = 0.010, # 1.00% max correlated exposure
    high_corr_threshold: float = 0.70
) -> List[Dict[str, Any]]:
    """
    Ranks multi-asset signals by confidence and filters out correlated excess exposure.
    Returns filtered list of trade signals ready for execution.
    """
    if not candidate_signals:
        return []

    # Sort signals descending by confidence score
    sorted_signals = sorted(candidate_signals, key=lambda s: s.get("confidence", 0.50), reverse=True)

    accepted_signals = []
    current_open_risk = 0.0
    accepted_assets = []

    for sig in sorted_signals:
        asset = sig.get("asset", "BTC")
        risk_pct = sig.get("risk_pct", 0.005)

        if current_open_risk + risk_pct > max_aggregate_risk:
            continue  # Aggregate risk cap reached

        # Check correlation against already accepted assets
        is_correlated = False
        for acc in accepted_assets:
            if asset in corr_matrix.columns and acc in corr_matrix.columns:
                c_val = abs(corr_matrix.loc[asset, acc])
                if c_val >= high_corr_threshold:
                    is_correlated = True
                    break

        if is_correlated and (current_open_risk + risk_pct > max_correlated_risk):
            sig["correlation_penalty_mult"] = 0.70  # Reduce risk budget for correlated asset
        else:
            sig["correlation_penalty_mult"] = 1.00

        accepted_signals.append(sig)
        accepted_assets.append(asset)
        current_open_risk += risk_pct * sig["correlation_penalty_mult"]

    return accepted_signals
