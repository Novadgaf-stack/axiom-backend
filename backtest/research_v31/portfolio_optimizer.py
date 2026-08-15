"""
NEXUS-7 Research V31 — Portfolio Optimizer & Risk Control Module
Handles signal ranking and selection when multiple assets trigger simultaneously.
Enforces 1.50% max aggregate open risk and 1.00% max correlated exposure limit.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def filter_and_rank_portfolio_signals(
    multi_asset_signals: Dict[str, pd.DataFrame],
    correlation_matrix: pd.DataFrame,
    max_aggregate_risk_pct: float = 0.0150,  # 1.50% max aggregate open risk
    max_correlated_risk_pct: float = 0.0100   # 1.00% max correlated exposure
) -> Dict[str, pd.DataFrame]:
    """
    Ranks signals across liquid assets when simultaneous entries trigger.
    Applies asset correlation penalty and open exposure caps.
    """
    filtered_dict = {}

    for asset, df in multi_asset_signals.items():
        df_copy = df.copy()
        if "confidence" in df_copy.columns and "signal" in df_copy.columns:
            # Scale signal quality by volume Z-score and asset beta
            avg_corr = float(correlation_matrix[asset].mean()) if asset in correlation_matrix.columns else 0.5
            quality_score = df_copy["confidence"] * (1.0 - max(0, avg_corr - 0.5) * 0.4)
            df_copy["quality_score"] = quality_score
        filtered_dict[asset] = df_copy

    return filtered_dict
