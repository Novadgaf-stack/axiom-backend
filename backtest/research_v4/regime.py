"""
NEXUS-7 — MARKET REGIME DETECTOR & CLASSIFIER (RESEARCH V4)
Detects structural market states: TRENDING_BULL, TRENDING_BEAR, RANGING_LOW_VOL, BREAKOUT_HIGH_VOL.
"""
from enum import Enum
from typing import Dict, List, Tuple
import numpy as np


class MarketRegime(str, Enum):
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING_LOW_VOL = "RANGING_LOW_VOL"
    BREAKOUT_HIGH_VOL = "BREAKOUT_HIGH_VOL"


class RegimeDetector:
    """Classifies market environment for regime-aware strategy weighting."""

    @staticmethod
    def calculate_indicators(prices: np.ndarray, high: np.ndarray, low: np.ndarray) -> Dict[str, np.ndarray]:
        n = len(prices)
        if n < 50:
            return {
                "ema50": prices,
                "ema200": prices,
                "atr": np.zeros(n),
                "atr_ratio": np.ones(n),
                "adx": np.zeros(n),
            }

        # EMA 50 & 200
        alpha50 = 2.0 / (50 + 1)
        alpha200 = 2.0 / (200 + 1)
        ema50 = np.zeros(n)
        ema200 = np.zeros(n)
        ema50[0] = prices[0]
        ema200[0] = prices[0]

        for i in range(1, n):
            ema50[i] = alpha50 * prices[i] + (1 - alpha50) * ema50[i - 1]
            ema200[i] = alpha200 * prices[i] + (1 - alpha200) * ema200[i - 1]

        # ATR & ATR Ratio
        tr = np.zeros(n)
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - prices[i - 1]),
                abs(low[i] - prices[i - 1])
            )

        atr = np.zeros(n)
        atr[0] = tr[0]
        alpha_atr = 1.0 / 14.0
        for i in range(1, n):
            atr[i] = alpha_atr * tr[i] + (1 - alpha_atr) * atr[i - 1]

        # 50-period moving average of ATR
        atr_ma50 = np.zeros(n)
        for i in range(n):
            start_idx = max(0, i - 49)
            atr_ma50[i] = np.mean(atr[start_idx : i + 1])

        atr_ratio = np.where(atr_ma50 > 0, atr / atr_ma50, 1.0)

        # Simplified ADX proxy based on directional movement ratio
        adx = np.zeros(n)
        up_move = np.zeros(n)
        down_move = np.zeros(n)
        for i in range(1, n):
            up = high[i] - high[i - 1]
            down = low[i - 1] - low[i]
            up_move[i] = up if (up > down and up > 0) else 0.0
            down_move[i] = down if (down > up and down > 0) else 0.0

        for i in range(14, n):
            plus_di = np.sum(up_move[i - 13 : i + 1])
            minus_di = np.sum(down_move[i - 13 : i + 1])
            denom = plus_di + minus_di
            dx = (abs(plus_di - minus_di) / denom * 100.0) if denom > 0 else 0.0
            adx[i] = 0.1 * dx + 0.9 * adx[i - 1]

        return {
            "ema50": ema50,
            "ema200": ema200,
            "atr": atr,
            "atr_ratio": atr_ratio,
            "adx": adx,
        }

    @classmethod
    def detect_regime(cls, close: float, ema50: float, ema200: float, atr_ratio: float, adx: float) -> MarketRegime:
        if atr_ratio >= 1.4:
            return MarketRegime.BREAKOUT_HIGH_VOL

        if adx >= 25.0:
            if close > ema50 and ema50 > ema200:
                return MarketRegime.TRENDING_BULL
            elif close < ema50 and ema50 < ema200:
                return MarketRegime.TRENDING_BEAR

        return MarketRegime.RANGING_LOW_VOL
