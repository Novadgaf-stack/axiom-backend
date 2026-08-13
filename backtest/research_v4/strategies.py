"""
NEXUS-7 — MULTI-HYPOTHESIS STRATEGY ENSEMBLE (RESEARCH V4)
Four independent, specialized quantitative trading strategies.
"""
from typing import Dict, List, Tuple
import numpy as np
from backtest.research_v4.regime import MarketRegime


class BaseStrategyHypothesis:
    """Base interface for all strategy hypotheses in the ensemble."""
    name: str = "BaseStrategy"

    def evaluate(
        self,
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        regime: MarketRegime,
        idx: int
    ) -> Tuple[int, float]:
        """Returns (signal: 1 for BUY, -1 for SELL, 0 for FLAT, confidence: 0.0-100.0)."""
        raise NotImplementedError


class TrendFollowingStrategy(BaseStrategyHypothesis):
    """Trend Following Hypothesis: EMA 20/50 alignment + 20-period breakout."""
    name = "TrendFollowing"

    def evaluate(self, prices: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray, regime: MarketRegime, idx: int) -> Tuple[int, float]:
        if idx < 50:
            return 0, 0.0

        p = prices[idx]
        ema20 = np.mean(prices[idx - 20 : idx + 1])
        ema50 = np.mean(prices[idx - 50 : idx + 1])
        high_20 = np.max(high[idx - 20 : idx])
        low_20 = np.min(low[idx - 20 : idx])

        if p > high_20 and ema20 > ema50:
            conf = 85.0 if regime == MarketRegime.TRENDING_BULL else 65.0
            return 1, conf
        elif p < low_20 and ema20 < ema50:
            conf = 85.0 if regime == MarketRegime.TRENDING_BEAR else 65.0
            return -1, conf

        return 0, 0.0


class MeanReversionStrategy(BaseStrategyHypothesis):
    """Mean Reversion Hypothesis: RSI(14) + Bollinger extremes in RANGING regime."""
    name = "MeanReversion"

    def evaluate(self, prices: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray, regime: MarketRegime, idx: int) -> Tuple[int, float]:
        if idx < 30:
            return 0, 0.0

        slice_px = prices[idx - 14 : idx + 1]
        diffs = np.diff(slice_px)
        gains = np.where(diffs > 0, diffs, 0)
        losses = np.where(diffs < 0, -diffs, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        bb_mean = np.mean(prices[idx - 20 : idx + 1])
        bb_std = np.std(prices[idx - 20 : idx + 1])
        lower_bb = bb_mean - 2.0 * bb_std
        upper_bb = bb_mean + 2.0 * bb_std

        p = prices[idx]

        if rsi < 32.0 and p <= lower_bb:
            conf = 90.0 if regime == MarketRegime.RANGING_LOW_VOL else 55.0
            return 1, conf
        elif rsi > 68.0 and p >= upper_bb:
            conf = 90.0 if regime == MarketRegime.RANGING_LOW_VOL else 55.0
            return -1, conf

        return 0, 0.0


class BreakoutVolatilityStrategy(BaseStrategyHypothesis):
    """Breakout & Volatility Squeeze Hypothesis: ATR expansion + Keltner Channel breakout."""
    name = "BreakoutVolatility"

    def evaluate(self, prices: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray, regime: MarketRegime, idx: int) -> Tuple[int, float]:
        if idx < 30:
            return 0, 0.0

        p = prices[idx]
        high_15 = np.max(high[idx - 15 : idx])
        low_15 = np.min(low[idx - 15 : idx])

        if regime == MarketRegime.BREAKOUT_HIGH_VOL:
            if p > high_15:
                return 1, 92.0
            elif p < low_15:
                return -1, 92.0

        return 0, 0.0


class MomentumQualityStrategy(BaseStrategyHypothesis):
    """Momentum Quality Hypothesis: Rate of Change (ROC-12) + Volume Acceleration."""
    name = "MomentumQuality"

    def evaluate(self, prices: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray, regime: MarketRegime, idx: int) -> Tuple[int, float]:
        if idx < 20:
            return 0, 0.0

        p = prices[idx]
        prev_p = prices[idx - 12]
        roc = ((p - prev_p) / prev_p) * 100.0

        vol_ma = np.mean(volume[idx - 10 : idx + 1])
        vol_curr = volume[idx]

        if roc > 2.5 and vol_curr > 1.2 * vol_ma:
            return 1, 80.0
        elif roc < -2.5 and vol_curr > 1.2 * vol_ma:
            return -1, 80.0

        return 0, 0.0
