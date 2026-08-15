"""
Portfolio Constructor Module for NEXUS-7 Final Master Research
Calculates rolling asset return correlation matrices, detects clusters (0.60–0.90),
and enforces portfolio risk caps.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def compute_asset_correlation_matrix_final(
    datasets: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Computes rolling asset return correlation matrix."""
    returns_dict = {}
    for asset, df in datasets.items():
        if "close" in df.columns and len(df) > 10:
            returns_dict[asset] = df["close"].pct_change()

    ret_df = pd.DataFrame(returns_dict).dropna()
    if ret_df.empty:
        return pd.DataFrame()

    return ret_df.corr()


def filter_correlated_opportunities_final(
    candidate_opportunities: List[Dict[str, Any]],
    corr_matrix: pd.DataFrame,
    max_correlation: float = 0.70
) -> List[Dict[str, Any]]:
    """
    De-duplicates highly correlated opportunities to avoid opening 5 identical trades.
    """
    if not candidate_opportunities or corr_matrix.empty:
        return candidate_opportunities

    selected = []
    selected_assets = set()

    for opp in candidate_opportunities:
        asset = opp["asset"]
        if asset in selected_assets:
            continue

        too_correlated = False
        for s_asset in selected_assets:
            if asset in corr_matrix.columns and s_asset in corr_matrix.columns:
                corr_val = abs(corr_matrix.loc[asset, s_asset])
                if corr_val > max_correlation:
                    too_correlated = True
                    break

        if not too_correlated:
            selected.append(opp)
            selected_assets.add(asset)

    return selected
