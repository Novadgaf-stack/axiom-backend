"""
NEXUS-7 — MULTI-TIMEFRAME & FEATURE ENGINE (RESEARCH V5)
Calculates 15m execution features, 1h regime indicators, and 4h macro directional bias.
"""
from typing import Dict, List, Tuple
import numpy as np


class MultiTimeframeFeatureEngine:
    """Computes multi-timeframe structural features and directional biases."""

    @staticmethod
    def compute_features(
        prices_15m: np.ndarray,
        high_15m: np.ndarray,
        low_15m: np.ndarray,
        volume_15m: np.ndarray
    ) -> Dict[str, np.ndarray]:
        n = len(prices_15m)
        if n < 100:
            return {
                "ema50_15m": prices_15m,
                "ema200_15m": prices_15m,
                "vwap_15m": prices_15m,
                "atr_ratio_15m": np.ones(n),
                "roc_12_15m": np.zeros(n),
                "bias_1h": np.zeros(n),
                "bias_4h": np.zeros(n),
                "volume_imbalance": np.ones(n),
            }

        # EMA 50 & 200 on 15m
        alpha50 = 2.0 / (50 + 1)
        alpha200 = 2.0 / (200 + 1)
        ema50 = np.zeros(n)
        ema200 = np.zeros(n)
        ema50[0] = prices_15m[0]
        ema200[0] = prices_15m[0]

        for i in range(1, n):
            ema50[i] = alpha50 * prices_15m[i] + (1 - alpha50) * ema50[i - 1]
            ema200[i] = alpha200 * prices_15m[i] + (1 - alpha200) * ema200[i - 1]

        # VWAP proxy (rolling 20 periods)
        vwap = np.zeros(n)
        for i in range(n):
            start = max(0, i - 19)
            pv = prices_15m[start : i + 1] * volume_15m[start : i + 1]
            v_sum = np.sum(volume_15m[start : i + 1])
            vwap[i] = (np.sum(pv) / v_sum) if v_sum > 0 else prices_15m[i]

        # ATR Ratio
        tr = np.zeros(n)
        tr[0] = high_15m[0] - low_15m[0]
        for i in range(1, n):
            tr[i] = max(
                high_15m[i] - low_15m[i],
                abs(high_15m[i] - prices_15m[i - 1]),
                abs(low_15m[i] - prices_15m[i - 1])
            )

        atr = np.zeros(n)
        atr[0] = tr[0]
        for i in range(1, n):
            atr[i] = (1.0 / 14.0) * tr[i] + (13.0 / 14.0) * atr[i - 1]

        atr_ma50 = np.zeros(n)
        for i in range(n):
            start = max(0, i - 49)
            atr_ma50[i] = np.mean(atr[start : i + 1])
        atr_ratio = np.where(atr_ma50 > 0, atr / atr_ma50, 1.0)

        # ROC-12
        roc = np.zeros(n)
        for i in range(12, n):
            roc[i] = ((prices_15m[i] - prices_15m[i - 12]) / prices_15m[i - 12]) * 100.0

        # Volume Imbalance Ratio (Volume / 20-period MA Volume)
        vol_ma20 = np.zeros(n)
        for i in range(n):
            start = max(0, i - 19)
            vol_ma20[i] = np.mean(volume_15m[start : i + 1])
        vol_imbalance = np.where(vol_ma20 > 0, volume_15m / vol_ma20, 1.0)

        # 1H & 4H Macro Bias Simulation (Resampled EMA trends)
        bias_1h = np.zeros(n)
        bias_4h = np.zeros(n)
        for i in range(n):
            # 1H bias (4 bars per 1h)
            h1_idx = max(0, i - 16)
            h1_ema = np.mean(prices_15m[h1_idx : i + 1])
            bias_1h[i] = 1.0 if prices_15m[i] > h1_ema else -1.0

            # 4H bias (16 bars per 4h)
            h4_idx = max(0, i - 64)
            h4_ema = np.mean(prices_15m[h4_idx : i + 1])
            bias_4h[i] = 1.0 if prices_15m[i] > h4_ema else -1.0

        return {
            "ema50_15m": ema50,
            "ema200_15m": ema200,
            "vwap_15m": vwap,
            "atr_15m": atr,
            "atr_ratio_15m": atr_ratio,
            "roc_12_15m": roc,
            "bias_1h": bias_1h,
            "bias_4h": bias_4h,
            "volume_imbalance": vol_imbalance,
        }
