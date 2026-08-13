"""
NEXUS-7 — MICROSTRUCTURE & PAIR ALPHA HYPOTHESES (RESEARCH V8)
Implements 3 novel non-ML microstructure and pair alpha hypotheses.
"""
from typing import Dict, Tuple
import numpy as np


class MicrostructureAlphaEngine:
    """Generates signals for 3 novel microstructure and pair alpha hypotheses."""

    @staticmethod
    def evaluate_volume_delta_absorption(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        flow: Dict[str, np.ndarray],
        i: int
    ) -> int:
        """
        Hypothesis V8-A: Volume Delta Absorption Divergence (VDAD)
        Triggers when price touches a 20-bar High/Low, but Cumulative Volume Delta (CVD) fails to make a new High/Low (passive absorption).
        """
        if i < 20:
            return 0

        high_20 = np.max(high[i - 20 : i])
        low_20 = np.min(low[i - 20 : i])

        cvd = flow["cvd"]
        cvd_max_20 = np.max(cvd[i - 20 : i])
        cvd_min_20 = np.min(cvd[i - 20 : i])

        # Bullish absorption: Price makes new 20-bar low, but CVD stays higher than 20-bar min (passive buy absorption)
        if low[i] <= low_20 and cvd[i] > cvd_min_20 * 0.998 and flow["imbalance_ratio"][i] > 1.2:
            return 1

        # Bearish absorption: Price makes new 20-bar high, but CVD stays lower than 20-bar max (passive sell absorption)
        if high[i] >= high_20 and cvd[i] < cvd_max_20 * 1.002 and flow["imbalance_ratio"][i] < 0.8:
            return -1

        return 0

    @staticmethod
    def evaluate_volume_delta_squeeze(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        flow: Dict[str, np.ndarray],
        i: int
    ) -> int:
        """
        Hypothesis V8-B: Volatility Compression + Volume Delta Surge (VDS)
        Triggers when low volatility ATR ratio (< 0.85) is followed by explosive CVD surge (|Z-Score| > 2.0).
        """
        if i < 20:
            return 0

        atr_ratios = features["atr_ratio_15m"][i - 12 : i]
        is_compressed = np.mean(atr_ratios) < 0.85
        cvd_z = flow["cvd_zscore"][i]
        bias_4h = features["bias_4h"][i]

        if is_compressed:
            if cvd_z > 2.0 and bias_4h == 1.0:
                return 1  # Aggressive buy market order breakout
            elif cvd_z < -2.0 and bias_4h == -1.0:
                return -1 # Aggressive sell market order breakout

        return 0

    @staticmethod
    def evaluate_pair_spread_reversion(
        prices_btc: np.ndarray,
        prices_eth: np.ndarray,
        i: int
    ) -> Tuple[int, int]:
        """
        Hypothesis V8-C: BTC/ETH Portfolio Pair Spread Reversion (PPSMR)
        Triggers mean-reversion trades when log-price spread strays > 2.2x rolling standard deviation from mean.
        Returns (btc_signal, eth_signal).
        """
        if i < 30:
            return 0, 0

        log_btc = np.log(prices_btc[i - 30 : i + 1])
        log_eth = np.log(prices_eth[i - 30 : i + 1])
        spread = log_btc - log_eth

        curr_spread = spread[-1]
        mean_spread = np.mean(spread[:-1])
        std_spread = np.std(spread[:-1])

        if std_spread <= 0:
            return 0, 0

        z_spread = (curr_spread - mean_spread) / std_spread

        # BTC overvalued relative to ETH -> Short BTC, Long ETH
        if z_spread > 2.2:
            return -1, 1
        # BTC undervalued relative to ETH -> Long BTC, Short ETH
        elif z_spread < -2.2:
            return 1, -1

        return 0, 0
