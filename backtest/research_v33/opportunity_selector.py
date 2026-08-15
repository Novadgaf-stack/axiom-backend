"""
Opportunity Selector Module for NEXUS-7 Research V33
Executes multi-stage portfolio opportunity selection:
Universe -> Liquidity Filter -> Regime Filter -> Signal -> Quality Ranking -> Correlation Filter -> Risk Filter -> Selected Trades.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def select_portfolio_opportunities(
    candidate_signals: List[Dict[str, Any]],
    corr_matrix: pd.DataFrame,
    max_aggregate_risk: float = 0.015,   # 1.50% max open risk
    max_correlated_risk: float = 0.010,  # 1.00% max correlated risk
    high_corr_threshold: float = 0.70
) -> List[Dict[str, Any]]:
    """
    Ranks multi-asset signals by measurable quality score and filters out correlated excess risk.
    Quality Score = confidence * 0.4 + (R_ratio / 2.0) * 0.3 + (1.0 / (1.0 + vol_penalty)) * 0.3
    """
    if not candidate_signals:
        return []

    # Calculate quality score for each candidate signal
    for sig in candidate_signals:
        conf = sig.get("confidence", 0.50)
        rr = sig.get("rr_ratio", 2.0)
        score = conf * 0.50 + min(1.0, rr / 2.0) * 0.50
        sig["quality_score"] = round(score, 3)

    # Sort signals descending by quality score
    sorted_signals = sorted(candidate_signals, key=lambda s: s["quality_score"], reverse=True)

    accepted = []
    accepted_assets = []
    current_open_risk = 0.0

    for sig in sorted_signals:
        asset = sig.get("asset", "BTC")
        risk_pct = sig.get("risk_pct", 0.005)

        if current_open_risk + risk_pct > max_aggregate_risk:
            continue  # Aggregate open risk cap reached

        # Check correlation against accepted assets
        is_correlated = False
        for acc in accepted_assets:
            if asset in corr_matrix.columns and acc in corr_matrix.columns:
                c_val = abs(corr_matrix.loc[asset, acc])
                if c_val >= high_corr_threshold:
                    is_correlated = True
                    break

        if is_correlated:
            if current_open_risk + risk_pct > max_correlated_risk:
                continue # Correlated exposure limit reached
            sig["correlation_penalty_mult"] = 0.70
        else:
            sig["correlation_penalty_mult"] = 1.00

        accepted.append(sig)
        accepted_assets.append(asset)
        current_open_risk += risk_pct * sig["correlation_penalty_mult"]

    return accepted
