"""
NEXUS-7 — MULTI-FACTOR CONSENSUS & QUALITY GATE (RESEARCH V4)
Combines independent strategy hypotheses using regime-compatible weighting matrices.
"""
from typing import Dict, List, Tuple
import numpy as np
from backtest.research_v4.regime import MarketRegime, RegimeDetector
from backtest.research_v4.strategies import (
    BaseStrategyHypothesis,
    TrendFollowingStrategy,
    MeanReversionStrategy,
    BreakoutVolatilityStrategy,
    MomentumQualityStrategy,
)


REGIME_WEIGHT_MATRIX: Dict[MarketRegime, Dict[str, float]] = {
    MarketRegime.TRENDING_BULL: {
        "TrendFollowing": 0.40,
        "MomentumQuality": 0.35,
        "BreakoutVolatility": 0.25,
        "MeanReversion": 0.00,
    },
    MarketRegime.TRENDING_BEAR: {
        "TrendFollowing": 0.40,
        "MomentumQuality": 0.35,
        "BreakoutVolatility": 0.25,
        "MeanReversion": 0.00,
    },
    MarketRegime.RANGING_LOW_VOL: {
        "MeanReversion": 0.50,
        "MomentumQuality": 0.25,
        "TrendFollowing": 0.25,
        "BreakoutVolatility": 0.00,
    },
    MarketRegime.BREAKOUT_HIGH_VOL: {
        "BreakoutVolatility": 0.50,
        "TrendFollowing": 0.30,
        "MomentumQuality": 0.20,
        "MeanReversion": 0.00,
    },
}


class StrategyConsensusEngine:
    """Combines ensemble strategies with regime-weighted voting."""

    def __init__(self):
        self.strategies: List[BaseStrategyHypothesis] = [
            TrendFollowingStrategy(),
            MeanReversionStrategy(),
            BreakoutVolatilityStrategy(),
            MomentumQualityStrategy(),
        ]

    def evaluate_consensus(
        self,
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        regime: MarketRegime,
        idx: int
    ) -> Dict:
        weights = REGIME_WEIGHT_MATRIX.get(regime, {})
        weighted_buy_score = 0.0
        weighted_sell_score = 0.0
        votes = {}

        for strat in self.strategies:
            sig, conf = strat.evaluate(prices, high, low, volume, regime, idx)
            w = weights.get(strat.name, 0.25)
            votes[strat.name] = {"signal": sig, "confidence": conf, "weight": w}

            if sig == 1:
                weighted_buy_score += (conf / 100.0) * w
            elif sig == -1:
                weighted_sell_score += (conf / 100.0) * w

        if weighted_buy_score > 0.35 and weighted_buy_score > weighted_sell_score:
            final_signal = 1
            final_conf = min(100.0, weighted_buy_score * 100.0)
        elif weighted_sell_score > 0.35 and weighted_sell_score > weighted_buy_score:
            final_signal = -1
            final_conf = min(100.0, weighted_sell_score * 100.0)
        else:
            final_signal = 0
            final_conf = 0.0

        return {
            "signal": final_signal,
            "confidence": round(final_conf, 1),
            "regime": regime.value,
            "weighted_buy": round(weighted_buy_score, 3),
            "weighted_sell": round(weighted_sell_score, 3),
            "votes": votes,
        }
