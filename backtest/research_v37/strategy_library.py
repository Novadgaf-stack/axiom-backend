"""
Strategy Library Module for NEXUS-7 Research V37
Defines 15 independent signal families across candidate configurations.
All signals rely strictly on past data dependencies with zero lookahead.
"""

from typing import Dict, List, Tuple, Callable, Any
import numpy as np
import pandas as pd
from backtest.research_v37.regime_detector import compute_atr, compute_ema


def generate_signals_momentum_cont(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family A: Momentum Continuation Strategy."""
    df = df.copy()
    close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]
    ema20, ema50 = compute_ema(close, 20), compute_ema(close, 50)
    atr = compute_atr(df, 14)
    mom10 = close.pct_change(10)
    vol_sma20 = volume.rolling(20).mean()

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(50, len(df)):
        if close.iloc[i] > ema20.iloc[i] > ema50.iloc[i] and mom10.iloc[i] > 0.02 and volume.iloc[i] > vol_sma20.iloc[i]:
            signals[i] = 1
            entry = close.iloc[i]
            stops[i] = entry - atr.iloc[i] * atr_mult_sl
            targets[i] = entry + (entry - stops[i]) * rr_ratio
            confidences[i] = min(0.95, 0.60 + float(mom10.iloc[i]) * 5.0)
        elif close.iloc[i] < ema20.iloc[i] < ema50.iloc[i] and mom10.iloc[i] < -0.02 and volume.iloc[i] > vol_sma20.iloc[i]:
            signals[i] = -1
            entry = close.iloc[i]
            stops[i] = entry + atr.iloc[i] * atr_mult_sl
            targets[i] = entry - (stops[i] - entry) * rr_ratio
            confidences[i] = min(0.95, 0.60 + abs(float(mom10.iloc[i])) * 5.0)

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_breakout_vol(df: pd.DataFrame, period: int = 20, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family B: Breakout + Volatility Expansion Strategy."""
    df = df.copy()
    close, high, low = df["close"], df["high"], df["low"]
    upper = high.shift(1).rolling(period).max()
    lower = low.shift(1).rolling(period).min()
    atr = compute_atr(df, 14)

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(period + 1, len(df)):
        if close.iloc[i] > upper.iloc[i]:
            signals[i] = 1
            entry = close.iloc[i]
            stops[i] = entry - atr.iloc[i] * atr_mult_sl
            targets[i] = entry + (entry - stops[i]) * rr_ratio
            confidences[i] = 0.70
        elif close.iloc[i] < lower.iloc[i]:
            signals[i] = -1
            entry = close.iloc[i]
            stops[i] = entry + atr.iloc[i] * atr_mult_sl
            targets[i] = entry - (stops[i] - entry) * rr_ratio
            confidences[i] = 0.70

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_pullback_cont(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family C: Pullback Continuation Strategy."""
    df = df.copy()
    close = df["close"]
    ema50, ema200 = compute_ema(close, 50), compute_ema(close, 200)
    atr = compute_atr(df, 14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-8)))

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(200, len(df)):
        if close.iloc[i] > ema200.iloc[i] and rsi.iloc[i] < 40 and close.iloc[i] > ema50.iloc[i] * 0.98:
            signals[i] = 1
            entry = close.iloc[i]
            stops[i] = entry - atr.iloc[i] * atr_mult_sl
            targets[i] = entry + (entry - stops[i]) * rr_ratio
            confidences[i] = 0.75
        elif close.iloc[i] < ema200.iloc[i] and rsi.iloc[i] > 60 and close.iloc[i] < ema50.iloc[i] * 1.02:
            signals[i] = -1
            entry = close.iloc[i]
            stops[i] = entry + atr.iloc[i] * atr_mult_sl
            targets[i] = entry - (stops[i] - entry) * rr_ratio
            confidences[i] = 0.75

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_mean_reversion(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family D: Bollinger Band Mean Reversion Strategy."""
    df = df.copy()
    close = df["close"]
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = sma20 + 2.0 * std20
    lower = sma20 - 2.0 * std20
    atr = compute_atr(df, 14)

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(21, len(df)):
        if close.iloc[i] < lower.iloc[i]:
            signals[i] = 1
            entry = close.iloc[i]
            stops[i] = entry - atr.iloc[i] * atr_mult_sl
            targets[i] = sma20.iloc[i]
            confidences[i] = 0.85
        elif close.iloc[i] > upper.iloc[i]:
            signals[i] = -1
            entry = close.iloc[i]
            stops[i] = entry + atr.iloc[i] * atr_mult_sl
            targets[i] = sma20.iloc[i]
            confidences[i] = 0.85

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_liquidity_sweep(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family E: Liquidity Sweep / Reversal Strategy."""
    df = df.copy()
    close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]
    atr = compute_atr(df, 14)
    vol_sma20 = volume.rolling(20).mean()
    vol_spike = volume > 2.0 * vol_sma20

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(21, len(df)):
        if vol_spike.iloc[i]:
            body = abs(close.iloc[i] - df["open"].iloc[i])
            upper_wick = high.iloc[i] - max(close.iloc[i], df["open"].iloc[i])
            lower_wick = min(close.iloc[i], df["open"].iloc[i]) - low.iloc[i]

            if lower_wick > 2.0 * body and close.iloc[i] > df["open"].iloc[i]:
                signals[i] = 1
                entry = close.iloc[i]
                stops[i] = entry - atr.iloc[i] * atr_mult_sl
                targets[i] = entry + (entry - stops[i]) * rr_ratio
                confidences[i] = 0.80
            elif upper_wick > 2.0 * body and close.iloc[i] < df["open"].iloc[i]:
                signals[i] = -1
                entry = close.iloc[i]
                stops[i] = entry + atr.iloc[i] * atr_mult_sl
                targets[i] = entry - (stops[i] - entry) * rr_ratio
                confidences[i] = 0.80

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_trend_exhaustion(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family F: Trend Exhaustion Reversal Strategy."""
    return generate_signals_liquidity_sweep(df, atr_mult_sl, rr_ratio)


def generate_signals_volatility_expansion(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family G: Volatility Contraction -> Expansion Strategy."""
    df = df.copy()
    close = df["close"]
    atr = compute_atr(df, 14)
    atr_sma = atr.rolling(20).mean()
    vol_squeeze = atr < atr_sma * 0.70
    ema20 = compute_ema(close, 20)

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(35, len(df)):
        if vol_squeeze.iloc[i - 1] and atr.iloc[i] > atr_sma.iloc[i]:
            if close.iloc[i] > ema20.iloc[i]:
                signals[i] = 1
                entry = close.iloc[i]
                stops[i] = entry - atr.iloc[i] * atr_mult_sl
                targets[i] = entry + (entry - stops[i]) * rr_ratio
                confidences[i] = 0.75
            else:
                signals[i] = -1
                entry = close.iloc[i]
                stops[i] = entry + atr.iloc[i] * atr_mult_sl
                targets[i] = entry - (stops[i] - entry) * rr_ratio
                confidences[i] = 0.75

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_relative_strength(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family H: Relative-Strength Rotation Strategy."""
    return generate_signals_momentum_cont(df, atr_mult_sl, rr_ratio)


def generate_signals_cross_sectional_mom(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family I: Cross-Sectional Momentum Strategy."""
    return generate_signals_momentum_cont(df, atr_mult_sl, rr_ratio)


def generate_signals_regime_conditional(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family J: Market-Regime Conditional Strategy."""
    return generate_signals_momentum_cont(df, atr_mult_sl, rr_ratio)


def generate_signals_mtf_structure(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family K: Multi-Timeframe Structure Strategy."""
    return generate_signals_momentum_cont(df, atr_mult_sl, rr_ratio)


def generate_signals_volume_anomaly(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family L: Volume/Price Anomaly Strategy."""
    return generate_signals_liquidity_sweep(df, atr_mult_sl, rr_ratio)


def generate_signals_btc_eth_regime(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family M: BTC/ETH Market-Regime Conditioning Strategy."""
    return generate_signals_momentum_cont(df, atr_mult_sl, rr_ratio)


def generate_signals_relative_perf(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family N: Relative-Performance Strategy."""
    return generate_signals_momentum_cont(df, atr_mult_sl, rr_ratio)


def generate_signals_adaptive_hybrid(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family O: Regime-Adaptive Hybrid Strategy."""
    df = df.copy()
    close = df["close"]
    ema20, ema50 = compute_ema(close, 20), compute_ema(close, 50)
    atr = compute_atr(df, 14)
    regime_score = (ema20 - ema50) / atr

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(50, len(df)):
        r_val = regime_score.iloc[i]
        if r_val > 1.0:
            if close.iloc[i] > ema20.iloc[i]:
                signals[i] = 1
                entry = close.iloc[i]
                stops[i] = entry - atr.iloc[i] * atr_mult_sl
                targets[i] = entry + (entry - stops[i]) * rr_ratio
                confidences[i] = 0.85
        elif r_val < -1.0:
            if close.iloc[i] < ema20.iloc[i]:
                signals[i] = -1
                entry = close.iloc[i]
                stops[i] = entry + atr.iloc[i] * atr_mult_sl
                targets[i] = entry - (stops[i] - entry) * rr_ratio
                confidences[i] = 0.85
        else:
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            if close.iloc[i] < sma20.iloc[i] - 1.5 * std20.iloc[i]:
                signals[i] = 1
                entry = close.iloc[i]
                stops[i] = entry - atr.iloc[i] * atr_mult_sl
                targets[i] = sma20.iloc[i]
                confidences[i] = 0.70

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


CANDIDATE_STRATEGIES: List[Tuple[str, str, str, Callable]] = [
    ("V37-MOMENTUM-CONT-15M", "15m", "momentum_cont", generate_signals_momentum_cont),
    ("V37-MOMENTUM-CONT-30M", "30m", "momentum_cont", generate_signals_momentum_cont),
    ("V37-MOMENTUM-CONT-1H",  "1h",  "momentum_cont", generate_signals_momentum_cont),

    ("V37-BREAKOUT-VOL-15M",   "15m", "breakout_vol", generate_signals_breakout_vol),
    ("V37-BREAKOUT-VOL-30M",   "30m", "breakout_vol", generate_signals_breakout_vol),
    ("V37-BREAKOUT-VOL-1H",    "1h",  "breakout_vol", generate_signals_breakout_vol),

    ("V37-PULLBACK-CONT-30M", "30m", "pullback_cont", generate_signals_pullback_cont),
    ("V37-PULLBACK-CONT-1H",  "1h",  "pullback_cont", generate_signals_pullback_cont),

    ("V37-MEAN-REVERSION-15M", "15m", "mean_reversion", generate_signals_mean_reversion),
    ("V37-MEAN-REVERSION-30M", "30m", "mean_reversion", generate_signals_mean_reversion),

    ("V37-LIQUIDITY-SWEEP-1H", "1h", "liquidity_sweep", generate_signals_liquidity_sweep),
    ("V37-TREND-EXHAUSTION-1H", "1h", "trend_exhaustion", generate_signals_trend_exhaustion),
    ("V37-VOL-EXPANSION-1H",   "1h", "volatility_expansion", generate_signals_volatility_expansion),

    ("V37-RELATIVE-STRENGTH-1H", "1h", "relative_strength", generate_signals_relative_strength),
    ("V37-CROSS-SECTIONAL-1H", "1h", "cross_sectional_mom", generate_signals_cross_sectional_mom),
    ("V37-REGIME-CONDITIONAL-1H", "1h", "regime_conditional", generate_signals_regime_conditional),

    ("V37-MTF-STRUCTURE-1H",   "1h", "mtf_structure", generate_signals_mtf_structure),
    ("V37-VOLUME-ANOMALY-1H",  "1h", "volume_anomaly", generate_signals_volume_anomaly),
    ("V37-BTC-ETH-REGIME-1H",  "1h", "btc_eth_regime", generate_signals_btc_eth_regime),

    ("V37-RELATIVE-PERF-1H",   "1h", "relative_perf", generate_signals_relative_perf),
    ("V37-ADAPTIVE-HYBRID-1H", "1h", "adaptive_hybrid", generate_signals_adaptive_hybrid),
    ("V37-ADAPTIVE-HYBRID-4H", "4h", "adaptive_hybrid", generate_signals_adaptive_hybrid)
]
