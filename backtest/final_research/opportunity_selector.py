"""
Opportunity Selector Module for NEXUS-7 Final Master Research
Dynamic portfolio-level opportunity scanner, continuous quality scoring (A+ to REJECT),
and selection policies (top 1, top 2, top 3, top 5, score threshold).
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from backtest.final_research.signal_engine import extract_signal_features_final


def generate_candidate_opportunities_final(
    datasets: Dict[str, pd.DataFrame],
    strategy_fn: Any,
    family_name: str = "momentum_cont",
    timeframe: str = "1h"
) -> List[Dict[str, Any]]:
    """
    Scans asset datasets and constructs structured candidate opportunity dictionaries.
    """
    opportunities = []

    for asset, df in datasets.items():
        df_sig = strategy_fn(df)
        non_zero_sigs = df_sig[df_sig["signal"] != 0]

        for idx, row in non_zero_sigs.iterrows():
            bar_idx = int(df.index.get_loc(idx)) if idx in df.index else 0
            sig_dir = int(row["signal"])
            entry = float(row["close"])
            stop = float(row["stop_loss"])
            target = float(row["take_profit"])

            features = extract_signal_features_final(df, bar_idx, sig_dir, entry, stop, target)

            opportunities.append({
                "timestamp": row["timestamp"],
                "asset": asset,
                "strategy_family": family_name,
                "timeframe": timeframe,
                "direction": "LONG" if sig_dir == 1 else "SHORT",
                "signal_dir": sig_dir,
                "entry_price": entry,
                "stop_loss": stop,
                "take_profit": target,
                "rr_ratio": features["rr_ratio"],
                "stop_distance": abs(entry - stop),
                "market_regime": features["regime"],
                "liquidity_state": "HIGH_LIQUIDITY",
                "volatility_state": features["volatility_regime"],
                "momentum_state": features["momentum_strength"],
                "trend_state": features["trend_quality"],
                "confidence": float(row.get("confidence", 0.50)),
                "features": features,
                "risk_pct": 0.0050
            })

    return opportunities


def compute_opportunity_score_final(
    opp: Dict[str, Any],
    feature_weights: Dict[str, float] = None
) -> Tuple[float, str]:
    """
    Computes continuous opportunity score and maps to quality tier.
    """
    if feature_weights is None:
        feature_weights = {
            "conf": 0.35,
            "rr": 0.25,
            "trend": 0.15,
            "vol": 0.15,
            "mtf": 0.10
        }

    conf = opp.get("confidence", 0.50)
    rr = opp.get("rr_ratio", 2.0)
    features = opp.get("features", {})
    trend = features.get("trend_quality", 0.70)
    vol = features.get("volume_expansion", 0.70)
    mtf = features.get("mtf_agreement", 0.70)

    score = (
        conf * feature_weights.get("conf", 0.35) +
        min(1.0, rr / 2.0) * feature_weights.get("rr", 0.25) +
        trend * feature_weights.get("trend", 0.15) +
        vol * feature_weights.get("vol", 0.15) +
        mtf * feature_weights.get("mtf", 0.10)
    )
    score_rounded = round(float(score), 3)

    if score_rounded >= 0.85:
        tier = "A+"
    elif score_rounded >= 0.75:
        tier = "A"
    elif score_rounded >= 0.65:
        tier = "B+"
    elif score_rounded >= 0.55:
        tier = "B"
    elif score_rounded >= 0.45:
        tier = "C"
    else:
        tier = "REJECT"

    return score_rounded, tier


def filter_and_rank_opportunities_final(
    candidate_opportunities: List[Dict[str, Any]],
    selection_policy: str = "TOP_5",
    feature_weights: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    Ranks and selects candidate opportunities based on selection policy:
    TOP_1, TOP_2, TOP_3, TOP_5, SCORE_THRESHOLD.
    """
    if not candidate_opportunities:
        return []

    scored_opps = []
    for opp in candidate_opportunities:
        score, tier = compute_opportunity_score_final(opp, feature_weights=feature_weights)
        if tier == "REJECT":
            continue
        opp_copy = opp.copy()
        opp_copy["opportunity_score"] = score
        opp_copy["quality_tier"] = tier
        scored_opps.append(opp_copy)

    sorted_opps = sorted(scored_opps, key=lambda s: s["opportunity_score"], reverse=True)
    n = len(sorted_opps)
    if n == 0:
        return []

    if selection_policy == "TOP_1":
        return sorted_opps[:1]
    elif selection_policy == "TOP_2":
        return sorted_opps[:2]
    elif selection_policy == "TOP_3":
        return sorted_opps[:3]
    elif selection_policy == "SCORE_THRESHOLD":
        return [s for s in sorted_opps if s["opportunity_score"] >= 0.70]
    else: # TOP_5
        return sorted_opps[:min(5, n)]
