"""
NEXUS-7 — STRUCTURAL ALPHA HYPOTHESES GENERATOR (RESEARCH V6)
Implements 4 clean, non-ML structural market edge hypotheses.
"""
from typing import Dict, List, Tuple
import numpy as np


class StructuralAlphaEngine:
    """Generates signals for 4 distinct non-ML structural hypotheses."""

    @staticmethod
    def evaluate_mtf_trend_pullback(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        i: int
    ) -> int:
        """
        Hypothesis 1: Multi-Timeframe Trend Pullback (MTF-TP)
        Triggers when 15m price pulls back to VWAP/EMA20 in strong 1H trend & 4H bias alignment.
        """
        if i < 50:
            return 0

        p = prices[i]
        vwap = features["vwap_15m"][i]
        bias_4h = features["bias_4h"][i]
        atr_ratio = features["atr_ratio_15m"][i]

        # Trend alignment + pullback condition
        if bias_4h == 1.0 and atr_ratio > 0.9:
            if low[i] <= vwap * 1.002 and p > vwap:
                return 1
        elif bias_4h == -1.0 and atr_ratio > 0.9:
            if high[i] >= vwap * 0.998 and p < vwap:
                return -1

        return 0

    @staticmethod
    def evaluate_liquidity_level_sweep(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        i: int
    ) -> int:
        """
        Hypothesis 2: Liquidity Level Sweep Reversal (LLSR)
        Triggers on 20-period High/Low sweeps with immediate rejection & volume surge.
        """
        if i < 20:
            return 0

        high_20 = np.max(high[i - 20 : i])
        low_20 = np.min(low[i - 20 : i])
        vol_surge = features["volume_imbalance"][i] > 1.3

        # Bullish sweep of 20-bar low with close back inside range
        if low[i] < low_20 and prices[i] > low_20 and vol_surge:
            return 1

        # Bearish sweep of 20-bar high with close back inside range
        if high[i] > high_20 and prices[i] < high_20 and vol_surge:
            return -1

        return 0

    @staticmethod
    def evaluate_volatility_expansion_breakout(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        i: int
    ) -> int:
        """
        Hypothesis 3: Volatility Compression & Breakout Expansion (VEB)
        Triggers when low volatility (compression) bursts into high ATR expansion with 4H bias.
        """
        if i < 20:
            return 0

        atr_ratios = features["atr_ratio_15m"][i - 12 : i]
        is_compressed = np.mean(atr_ratios) < 0.85
        curr_expansion = features["atr_ratio_15m"][i] > 1.3
        bias_4h = features["bias_4h"][i]

        if is_compressed and curr_expansion:
            if bias_4h == 1.0 and prices[i] > features["ema50_15m"][i]:
                return 1
            elif bias_4h == -1.0 and prices[i] < features["ema50_15m"][i]:
                return -1

        return 0

    @staticmethod
    def evaluate_extremum_vwap_mean_reversion(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        i: int
    ) -> int:
        """
        Hypothesis 4: Extremum VWAP Mean Reversion (EVMR)
        Triggers counter-trend mean reversion in low-ADX/ranging regimes when price > 2.0x ATR from VWAP.
        """
        if i < 20:
            return 0

        atr = features.get("atr_15m", np.ones(len(prices)))[i]
        vwap = features["vwap_15m"][i]
        dist = prices[i] - vwap

        # Range regime condition: low ATR expansion
        if features["atr_ratio_15m"][i] < 1.0:
            if dist < -2.0 * atr:
                return 1  # Oversold long
            elif dist > 2.0 * atr:
                return -1 # Overbought short

        return 0
