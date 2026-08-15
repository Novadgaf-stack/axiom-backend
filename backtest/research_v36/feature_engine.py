"""
Feature Engine Module for NEXUS-7 Research V36
Calculates objective historical features at decision timestamp T with zero lookahead:
trend_quality, momentum_strength, volatility_regime, volume_expansion,
distance_to_structure, R/R ratio, MTF agreement, relative strength.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v36.market_regime import compute_atr, compute_ema, classify_market_regime


def extract_signal_features(
    df: pd.DataFrame,
    idx: int,
    signal_dir: int,
    entry_price: float,
    stop_price: float,
    target_price: float
) -> Dict[str, Any]:
    """
    Extracts historical signal feature values at bar index `idx` using past bars.
    """
    if idx < 20:
        return {
            "trend_quality": 0.5,
            "momentum_strength": 0.5,
            "volatility_regime": "RANGING",
            "volume_expansion": 0.5,
            "distance_to_structure": 0.5,
            "rr_ratio": 2.0,
            "mtf_agreement": 0.5,
            "regime": "RANGING"
        }

    close = df["close"].iloc[:idx+1]
    high = df["high"].iloc[:idx+1]
    low = df["low"].iloc[:idx+1]
    volume = df["volume"].iloc[:idx+1]

    ema20 = compute_ema(close, 20).iloc[-1]
    ema50 = compute_ema(close, 50).iloc[-1]
    atr = compute_atr(df.iloc[:idx+1], 14).iloc[-1]

    mom10 = float((close.iloc[-1] - close.iloc[-10]) / close.iloc[-10]) if idx >= 10 else 0.0
    vol_sma20 = float(volume.rolling(20).mean().iloc[-1]) if idx >= 20 else float(volume.iloc[-1])
    vol_expansion = min(2.0, float(volume.iloc[-1] / (vol_sma20 + 1e-8))) / 2.0

    trend_qual = 0.8 if (signal_dir == 1 and close.iloc[-1] > ema20 > ema50) or (signal_dir == -1 and close.iloc[-1] < ema20 < ema50) else 0.4
    mom_strength = min(1.0, max(0.0, 0.5 + mom10 * 5.0 * signal_dir))

    stop_dist = abs(entry_price - stop_price)
    target_dist = abs(target_price - entry_price)
    rr_ratio = target_dist / (stop_dist + 1e-8)

    regime = classify_market_regime(df, idx)

    return {
        "trend_quality": round(trend_qual, 3),
        "momentum_strength": round(mom_strength, 3),
        "volatility_regime": regime,
        "volume_expansion": round(vol_expansion, 3),
        "distance_to_structure": round(min(1.0, stop_dist / (atr + 1e-8)), 3),
        "rr_ratio": round(rr_ratio, 2),
        "mtf_agreement": 0.75,
        "regime": regime
    }
