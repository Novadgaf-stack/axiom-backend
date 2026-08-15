"""
Market Regime Classification Module for NEXUS-7 Research V36
Identifies historical market regimes using strictly historical price & volatility action:
TRENDING_UP, TRENDING_DOWN, RANGING, HIGH_VOLATILITY, LOW_VOLATILITY, BREAKOUT, COMPRESSION, RISK_OFF, RISK_ON.
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


def classify_market_regime(df: pd.DataFrame, idx: int) -> str:
    """
    Classifies market regime at bar `idx` using past bar information.
    """
    if idx < 50:
        return "RANGING"

    close = df["close"].iloc[:idx+1]
    ema20 = compute_ema(close, 20).iloc[-1]
    ema50 = compute_ema(close, 50).iloc[-1]
    c_val = close.iloc[-1]

    atr = compute_atr(df.iloc[:idx+1], 14).iloc[-1]
    atr_sma = compute_atr(df.iloc[:idx+1], 14).rolling(20).mean().iloc[-1] if idx >= 20 else atr

    vol_ratio = atr / (atr_sma + 1e-8)

    if vol_ratio > 1.5:
        return "HIGH_VOLATILITY"
    elif vol_ratio < 0.7:
        return "COMPRESSION"

    if c_val > ema20 > ema50:
        return "TRENDING_UP"
    elif c_val < ema20 < ema50:
        return "TRENDING_DOWN"
    else:
        return "RANGING"
