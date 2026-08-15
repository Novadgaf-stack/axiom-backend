"""
Regime Detector Module for NEXUS-7 Research V37
Identifies historical market regimes using strictly historical price, volatility, volume, and correlation action:
Trending, Ranging, High/Low Volatility, High/Low Volume, Bull/Bear/Neutral, BTC-led vs Alt-led, High/Low Correlation.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Computes Average True Range (ATR)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1).fillna(close)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().fillna(tr)


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Computes Exponential Moving Average (EMA)."""
    return series.ewm(span=period, adjust=False).mean()


def classify_market_regime(df: pd.DataFrame, idx: int) -> Dict[str, Any]:
    """
    Classifies market regime at bar `idx` using past bar information.
    """
    if idx < 50:
        return {
            "trend_regime": "RANGING",
            "volatility_regime": "NORMAL_VOLATILITY",
            "volume_regime": "NORMAL_VOLUME",
            "market_state": "NEUTRAL"
        }

    close = df["close"].iloc[:idx+1]
    volume = df["volume"].iloc[:idx+1]
    ema20 = compute_ema(close, 20).iloc[-1]
    ema50 = compute_ema(close, 50).iloc[-1]
    c_val = close.iloc[-1]

    atr = compute_atr(df.iloc[:idx+1], 14).iloc[-1]
    atr_sma = compute_atr(df.iloc[:idx+1], 14).rolling(20).mean().iloc[-1] if idx >= 20 else atr
    vol_ratio = atr / (atr_sma + 1e-8)

    vol_sma20 = float(volume.rolling(20).mean().iloc[-1]) if idx >= 20 else float(volume.iloc[-1])
    vol_expansion = float(volume.iloc[-1] / (vol_sma20 + 1e-8))

    if c_val > ema20 > ema50:
        trend_regime = "TRENDING_UP"
        market_state = "BULL"
    elif c_val < ema20 < ema50:
        trend_regime = "TRENDING_DOWN"
        market_state = "BEAR"
    else:
        trend_regime = "RANGING"
        market_state = "NEUTRAL"

    if vol_ratio > 1.5:
        vol_regime = "HIGH_VOLATILITY"
    elif vol_ratio < 0.7:
        vol_regime = "LOW_VOLATILITY"
    else:
        vol_regime = "NORMAL_VOLATILITY"

    if vol_expansion > 1.5:
        volume_regime = "HIGH_VOLUME"
    elif vol_expansion < 0.7:
        volume_regime = "LOW_VOLUME"
    else:
        volume_regime = "NORMAL_VOLUME"

    return {
        "trend_regime": trend_regime,
        "volatility_regime": vol_regime,
        "volume_regime": volume_regime,
        "market_state": market_state
    }
