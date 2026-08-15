"""
Opportunity Selector & Quality Scoring Module for NEXUS-7 Research V35
Executes multi-stage cross-asset opportunity quality scoring and bucketing (A+, A, B+, B, C, REJECT).
Evaluates selectivity thresholds (Percentiles: 100%, 75%, 50%, 30%, 20%, 10%, 5%; Top-K: 1, 2, 3, 5).
Includes feature ablation testing to isolate component contributions.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def compute_opportunity_score(
    sig: Dict[str, Any],
    feature_weights: Dict[str, float] = None
) -> Tuple[float, str]:
    """
    Computes objective cross-asset opportunity score and maps to quality tier:
    Score = conf * w_conf + min(1.0, rr/2.0) * w_rr + trend_qual * w_trend + vol_confirm * w_vol + mtf_agree * w_mtf
    Default weights: conf (0.35), rr (0.25), trend (0.15), vol (0.15), mtf (0.10)
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

    conf = sig.get("confidence", 0.50)
    rr = sig.get("rr_ratio", 2.0)
    trend_qual = sig.get("trend_quality", 0.70)
    vol_confirm = sig.get("volume_confirm", 0.70)
    mtf_agree = sig.get("mtf_agreement", 0.70)

    score = (
        conf * feature_weights.get("conf", 0.35) +
        min(1.0, rr / 2.0) * feature_weights.get("rr", 0.25) +
        trend_qual * feature_weights.get("trend", 0.15) +
        vol_confirm * feature_weights.get("vol", 0.15) +
        mtf_agree * feature_weights.get("mtf", 0.10)
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
    candidate_signals: List[Dict[str, Any]],
    selectivity_mode: str = "TOP_100PCT",
    feature_weights: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    Scores, ranks, and filters candidate signals based on selectivity mode:
    Percentiles: TOP_100PCT, TOP_75PCT, TOP_50PCT, TOP_30PCT, TOP_20PCT, TOP_10PCT, TOP_5PCT
    Quality Tiers: A_PLUS_ONLY, A_ONLY
    Top-K per bar: TOP_1, TOP_2, TOP_3, TOP_5
    """
    if not candidate_signals:
        return []

    scored_signals = []
    for sig in candidate_signals:
        score, tier = compute_opportunity_score(sig, feature_weights=feature_weights)
        if tier == "REJECT":
            continue
        sig_copy = sig.copy()
        sig_copy["opportunity_score"] = score
        sig_copy["quality_tier"] = tier
        scored_signals.append(sig_copy)

    sorted_signals = sorted(scored_signals, key=lambda s: s["opportunity_score"], reverse=True)
    n = len(sorted_signals)
    if n == 0:
        return []

    if selectivity_mode == "A_PLUS_ONLY":
        return [s for s in sorted_signals if s["quality_tier"] == "A+"]
    elif selectivity_mode == "A_ONLY":
        return [s for s in sorted_signals if s["quality_tier"] in ["A+", "A"]]
    elif selectivity_mode == "TOP_75PCT":
        return sorted_signals[:max(1, int(n * 0.75))]
    elif selectivity_mode == "TOP_50PCT":
        return sorted_signals[:max(1, int(n * 0.50))]
    elif selectivity_mode == "TOP_30PCT":
        return sorted_signals[:max(1, int(n * 0.30))]
    elif selectivity_mode == "TOP_20PCT":
        return sorted_signals[:max(1, int(n * 0.20))]
    elif selectivity_mode == "TOP_10PCT":
        return sorted_signals[:max(1, int(n * 0.10))]
    elif selectivity_mode == "TOP_5PCT":
        return sorted_signals[:max(1, int(n * 0.05))]
    elif selectivity_mode == "TOP_1":
        return sorted_signals[:1]
    elif selectivity_mode == "TOP_2":
        return sorted_signals[:2]
    elif selectivity_mode == "TOP_3":
        return sorted_signals[:3]
    elif selectivity_mode == "TOP_5":
        return sorted_signals[:5]
    else: # TOP_100PCT / ALL
        return sorted_signals


def run_feature_ablation_testing(
    candidate_signals: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Evaluates impact of removing individual scoring features one at a time.
    """
    feature_sets = {
        "FULL_SCORER": {"conf": 0.35, "rr": 0.25, "trend": 0.15, "vol": 0.15, "mtf": 0.10},
        "WITHOUT_TREND": {"conf": 0.40, "rr": 0.30, "trend": 0.00, "vol": 0.15, "mtf": 0.15},
        "WITHOUT_VOL": {"conf": 0.40, "rr": 0.30, "trend": 0.15, "vol": 0.00, "mtf": 0.15},
        "WITHOUT_MTF": {"conf": 0.40, "rr": 0.30, "trend": 0.15, "vol": 0.15, "mtf": 0.00},
        "WITHOUT_RR": {"conf": 0.55, "rr": 0.00, "trend": 0.15, "vol": 0.15, "mtf": 0.15}
    }

    results = {}
    for f_name, weights in feature_sets.items():
        results[f_name] = filter_and_rank_opportunities(candidate_signals, selectivity_mode="TOP_50PCT", feature_weights=weights)
    return results
