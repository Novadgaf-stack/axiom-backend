"""
Opportunity Ranker & Quality Scoring Module for NEXUS-7 Research V36
Scores and ranks opportunities using strictly historical features available at timestamp T.
Applies selectivity thresholds: TOP 100%, TOP 75%, TOP 50%, TOP 30%, TOP 20%, TOP 10%, TOP 5%.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def compute_opportunity_score(
    opp: Dict[str, Any],
    feature_weights: Dict[str, float] = None
) -> Tuple[float, str]:
    """
    Computes cross-asset opportunity score and maps to quality tier:
    Score = conf * w_conf + min(1.0, rr/2.0) * w_rr + trend * w_trend + vol * w_vol + mtf * w_mtf
    Quality Tiers:
    - A+: Score >= 0.85
    - A : 0.75 <= Score < 0.85
    - B+: 0.65 <= Score < 0.75
    - B : 0.55 <= Score < 0.65
    - C : 0.45 <= Score < 0.55
    - REJECT: Score < 0.45
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


def filter_and_rank_opportunities(
    candidate_opportunities: List[Dict[str, Any]],
    selectivity_mode: str = "TOP_100PCT",
    feature_weights: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    Scores, ranks, and filters candidate opportunities based on selectivity mode:
    TOP_100PCT, TOP_75PCT, TOP_50PCT, TOP_30PCT, TOP_20PCT, TOP_10PCT, TOP_5PCT.
    """
    if not candidate_opportunities:
        return []

    scored_opps = []
    for opp in candidate_opportunities:
        score, tier = compute_opportunity_score(opp, feature_weights=feature_weights)
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

    if selectivity_mode == "TOP_75PCT":
        return sorted_opps[:max(1, int(n * 0.75))]
    elif selectivity_mode == "TOP_50PCT":
        return sorted_opps[:max(1, int(n * 0.50))]
    elif selectivity_mode == "TOP_30PCT":
        return sorted_opps[:max(1, int(n * 0.30))]
    elif selectivity_mode == "TOP_20PCT":
        return sorted_opps[:max(1, int(n * 0.20))]
    elif selectivity_mode == "TOP_10PCT":
        return sorted_opps[:max(1, int(n * 0.10))]
    elif selectivity_mode == "TOP_5PCT":
        return sorted_opps[:max(1, int(n * 0.05))]
    else: # TOP_100PCT
        return sorted_opps
