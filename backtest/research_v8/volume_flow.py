"""
NEXUS-7 — VOLUME FLOW & ORDER IMBALANCE ENGINE (RESEARCH V8)
Calculates Volume Delta, Cumulative Volume Delta (CVD), and Order Imbalance Ratios.
"""
from typing import Dict
import numpy as np


class VolumeFlowEngine:
    """Computes order flow imbalance, Volume Delta, and Cumulative Volume Delta (CVD)."""

    @staticmethod
    def compute_volume_flow(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray
    ) -> Dict[str, np.ndarray]:
        n = len(prices)
        if n < 20:
            return {
                "vol_delta": np.zeros(n),
                "cvd": np.zeros(n),
                "imbalance_ratio": np.ones(n),
                "cvd_zscore": np.zeros(n),
            }

        # Estimate buying vs selling volume using candle range location
        range_hl = np.where((high - low) > 0, high - low, 1e-6)
        buy_pct = (prices - low) / range_hl
        buy_pct = np.clip(buy_pct, 0.05, 0.95)
        sell_pct = 1.0 - buy_pct

        vol_buy = volume * buy_pct
        vol_sell = volume * sell_pct

        vol_delta = vol_buy - vol_sell
        cvd = np.cumsum(vol_delta)

        imbalance_ratio = np.where(vol_sell > 0, vol_buy / vol_sell, 1.0)

        # Compute 20-period CVD Z-Score
        cvd_zscore = np.zeros(n)
        for i in range(20, n):
            sub_cvd = cvd[i - 20 : i]
            std = np.std(sub_cvd)
            if std > 0:
                cvd_zscore[i] = (cvd[i] - np.mean(sub_cvd)) / std

        return {
            "vol_buy": vol_buy,
            "vol_sell": vol_sell,
            "vol_delta": vol_delta,
            "cvd": cvd,
            "imbalance_ratio": imbalance_ratio,
            "cvd_zscore": cvd_zscore,
        }
