"""
Correlation & Portfolio Selector Module for NEXUS-7 Research V37
Handles correlation matrix computation, cluster detection (0.60–0.90 thresholds),
and enforces aggregate open risk caps, correlated risk caps, and concentration limits.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def detect_correlation_clusters(
    corr_df: pd.DataFrame,
    threshold: float = 0.70
) -> Dict[str, List[str]]:
    """
    Detects correlation clusters using a simple threshold graph components algorithm.
    """
    if corr_df.empty:
        return {}

    assets = list(corr_df.columns)
    visited = set()
    clusters = {}
    cluster_id = 1

    for a in assets:
        if a not in visited:
            cluster_members = [a]
            visited.add(a)
            for b in assets:
                if b != a and b not in visited:
                    if corr_df.loc[a, b] >= threshold:
                        cluster_members.append(b)
                        visited.add(b)
            clusters[f"CLUSTER_{cluster_id}"] = cluster_members
            cluster_id += 1

    return clusters


def enforce_portfolio_risk_caps(
    opportunities: List[Dict[str, Any]],
    corr_df: pd.DataFrame,
    max_simultaneous_positions: int = 5,
    max_aggregate_risk_pct: float = 0.015, # 1.5% max aggregate open risk
    max_cluster_risk_pct: float = 0.010,   # 1.0% max cluster risk
    max_asset_risk_pct: float = 0.0050,    # 0.50% max asset risk
    cluster_threshold: float = 0.70
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Selects non-correlated, risk-capped portfolio opportunities.
    """
    if not opportunities:
        return [], {"selected_count": 0, "rejected_count": 0, "total_risk_pct": 0.0}

    clusters = detect_correlation_clusters(corr_df, threshold=cluster_threshold)
    asset_to_cluster = {}
    for c_id, members in clusters.items():
        for m in members:
            asset_to_cluster[m] = c_id

    selected = []
    rejected_count = 0
    total_risk = 0.0
    cluster_risk = {}
    asset_risk = {}

    for opp in opportunities:
        if len(selected) >= max_simultaneous_positions:
            rejected_count += 1
            continue

        asset = opp["asset"]
        opp_risk = opp.get("risk_pct", 0.0050)

        if total_risk + opp_risk > max_aggregate_risk_pct:
            rejected_count += 1
            continue

        c_id = asset_to_cluster.get(asset, "DEFAULT_CLUSTER")
        c_risk = cluster_risk.get(c_id, 0.0)
        if c_risk + opp_risk > max_cluster_risk_pct:
            rejected_count += 1
            continue

        a_risk = asset_risk.get(asset, 0.0)
        if a_risk + opp_risk > max_asset_risk_pct:
            rejected_count += 1
            continue

        selected.append(opp)
        total_risk += opp_risk
        cluster_risk[c_id] = c_risk + opp_risk
        asset_risk[asset] = a_risk + opp_risk

    metrics = {
        "selected_count": len(selected),
        "rejected_count": rejected_count,
        "total_risk_pct": round(total_risk, 4),
        "cluster_count": len(clusters)
    }

    return selected, metrics
