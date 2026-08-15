"""
Opportunity Selector Module for NEXUS-7 Research V34
Executes multi-stage cross-asset opportunity ranking and quality bucketing (A+, A, B+, B, C, REJECT).
Evaluates selectivity filtering (All, A-only, A+/A-only, Top 1, Top 2, Top 3, Top 5).
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


def compute_opportunity_score(sig: Dict[str, Any]) -> Tuple[float, str]:
    """
    Computes objective cross-asset opportunity score and maps to quality tier:
    Score = conf * 0.40 + min(1.0, rr/2.0) * 0.30 + trend_qual * 0.15 + vol_confirm * 0.15
    Quality Tiers:
    - A+: Score >= 0.85
    - A : 0.75 <= Score < 0.85
    - B+: 0.65 <= Score < 0.75
    - B : 0.55 <= Score < 0.65
    - C : 0.45 <= Score < 0.55
    - REJECT: Score < 0.45
    """
    conf = sig.get("confidence", 0.50)
    rr = sig.get("rr_ratio", 2.0)
    trend_qual = sig.get("trend_quality", 0.70)
    vol_confirm = sig.get("volume_confirm", 0.70)

    score = conf * 0.40 + min(1.0, rr / 2.0) * 0.30 + trend_qual * 0.15 + vol_confirm * 0.15
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
    selectivity_mode: str = "ALL"
) -> List[Dict[str, Any]]:
    """
    Scores, ranks, and filters candidate signals based on selectivity mode:
    - ALL: all non-rejected signals
    - A_ONLY: A and A+ signals only
    - A_PLUS_ONLY: A+ signals only
    - TOP_1: top 1 signal per bar
    - TOP_2: top 2 signals per bar
    - TOP_3: top 3 signals per bar
    - TOP_5: top 5 signals per bar
    """
    if not candidate_signals:
        return []

    scored_signals = []
    for sig in candidate_signals:
        score, tier = compute_opportunity_score(sig)
        if tier == "REJECT":
            continue
        sig_copy = sig.copy()
        sig_copy["opportunity_score"] = score
        sig_copy["quality_tier"] = tier
        scored_signals.append(sig_copy)

    # Sort descending by score
    sorted_signals = sorted(scored_signals, key=lambda s: s["opportunity_score"], reverse=True)

    if selectivity_mode == "A_PLUS_ONLY":
        return [s for s in sorted_signals if s["quality_tier"] == "A+"]
    elif selectivity_mode == "A_ONLY":
        return [s for s in sorted_signals if s["quality_tier"] in ["A+", "A"]]
    elif selectivity_mode == "TOP_1":
        return sorted_signals[:1]
    elif selectivity_mode == "TOP_2":
        return sorted_signals[:2]
    elif selectivity_mode == "TOP_3":
        return sorted_signals[:3]
    elif selectivity_mode == "TOP_5":
        return sorted_signals[:5]
    else: # ALL
        return sorted_signals
