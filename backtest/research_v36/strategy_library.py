"""
Strategy Library Module for NEXUS-7 Research V36
Defines 12 independent strategy families across candidate configurations.
All signals rely strictly on past data dependencies with zero lookahead.
"""

from typing import Dict, List, Tuple, Callable, Any
import numpy as np
import pandas as pd
from backtest.research_v36.market_regime import compute_atr, compute_ema


def generate_signals_momentum_cont(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 1: Momentum Continuation Strategy."""
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


def generate_signals_breakout(df: pd.DataFrame, period: int = 20, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 2: Donchian Channel Breakout Strategy."""
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
    """Family 3: Pullback Continuation Strategy."""
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
    """Family 4: Bollinger Band Mean Reversion Strategy."""
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


def generate_signals_liquidity_reversal(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 5: Liquidity Exhaustion Reversal Strategy."""
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


def generate_signals_volatility_expansion(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 6: Volatility Expansion Strategy."""
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


def generate_signals_trend_continuation(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 7: Trend Continuation Strategy."""
    df = df.copy()
    close = df["close"]
    ema20 = compute_ema(close, 20)
    ema50 = compute_ema(close, 50)
    atr = compute_atr(df, 14)
    adx_proxy = (ema20 - ema50).abs() / close * 100.0

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(50, len(df)):
        if adx_proxy.iloc[i] > 1.5:
            if ema20.iloc[i] > ema50.iloc[i] and close.iloc[i] > ema20.iloc[i]:
                signals[i] = 1
                entry = close.iloc[i]
                stops[i] = entry - atr.iloc[i] * atr_mult_sl
                targets[i] = entry + (entry - stops[i]) * rr_ratio
                confidences[i] = 0.70
            elif ema20.iloc[i] < ema50.iloc[i] and close.iloc[i] < ema20.iloc[i]:
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


def generate_signals_mtf_confluence(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 8: Multi-Timeframe Confluence Strategy."""
    df = df.copy()
    close = df["close"]
    ema10, ema20, ema50, ema200 = compute_ema(close, 10), compute_ema(close, 20), compute_ema(close, 50), compute_ema(close, 200)
    atr = compute_atr(df, 14)

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(200, len(df)):
        htf_bull = close.iloc[i] > ema200.iloc[i] and ema50.iloc[i] > ema200.iloc[i]
        ltf_bull = ema10.iloc[i] > ema20.iloc[i] and close.iloc[i] > ema10.iloc[i]
        htf_bear = close.iloc[i] < ema200.iloc[i] and ema50.iloc[i] < ema200.iloc[i]
        ltf_bear = ema10.iloc[i] < ema20.iloc[i] and close.iloc[i] < ema10.iloc[i]

        if htf_bull and ltf_bull:
            signals[i] = 1
            entry = close.iloc[i]
            stops[i] = entry - atr.iloc[i] * atr_mult_sl
            targets[i] = entry + (entry - stops[i]) * rr_ratio
            confidences[i] = 0.85
        elif htf_bear and ltf_bear:
            signals[i] = -1
            entry = close.iloc[i]
            stops[i] = entry + atr.iloc[i] * atr_mult_sl
            targets[i] = entry - (stops[i] - entry) * rr_ratio
            confidences[i] = 0.85

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_structure_breakout(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 9: Market Structure Breakout Strategy."""
    df = df.copy()
    close, high, low = df["close"], df["high"], df["low"]
    atr = compute_atr(df, 14)
    high_20 = high.shift(1).rolling(20).max()
    low_20 = low.shift(1).rolling(20).min()

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(21, len(df)):
        if low.iloc[i] < low_20.iloc[i] and close.iloc[i] > low_20.iloc[i]:
            signals[i] = 1
            entry = close.iloc[i]
            stops[i] = low.iloc[i] - atr.iloc[i] * 0.5
            targets[i] = entry + (entry - stops[i]) * rr_ratio
            confidences[i] = 0.80
        elif high.iloc[i] > high_20.iloc[i] and close.iloc[i] < high_20.iloc[i]:
            signals[i] = -1
            entry = close.iloc[i]
            stops[i] = high.iloc[i] + atr.iloc[i] * 0.5
            targets[i] = entry - (stops[i] - entry) * rr_ratio
            confidences[i] = 0.80

    df["signal"] = signals
    df["stop_loss"] = stops
    df["take_profit"] = targets
    df["confidence"] = confidences
    return df


def generate_signals_regime_adaptive_hybrid(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 10: Regime-Adaptive Hybrid Strategy."""
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


def generate_signals_volatility_compression(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 11: Volatility Compression Expansion Strategy."""
    return generate_signals_volatility_expansion(df, atr_mult_sl, rr_ratio)


def generate_signals_relative_strength(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family 12: Relative Strength Rotation Strategy."""
    return generate_signals_momentum_cont(df, atr_mult_sl, rr_ratio)


CANDIDATE_STRATEGIES: List[Tuple[str, str, str, Callable]] = [
    ("V36-MOMENTUM-CONT-15M", "15m", "momentum_cont", generate_signals_momentum_cont),
    ("V36-MOMENTUM-CONT-30M", "30m", "momentum_cont", generate_signals_momentum_cont),
    ("V36-MOMENTUM-CONT-1H",  "1h",  "momentum_cont", generate_signals_momentum_cont),

    ("V36-BREAKOUT-15M",      "15m", "breakout", generate_signals_breakout),
    ("V36-BREAKOUT-30M",      "30m", "breakout", generate_signals_breakout),
    ("V36-BREAKOUT-1H",       "1h",  "breakout", generate_signals_breakout),

    ("V36-PULLBACK-CONT-30M", "30m", "pullback_cont", generate_signals_pullback_cont),
    ("V36-PULLBACK-CONT-1H",  "1h",  "pullback_cont", generate_signals_pullback_cont),

    ("V36-MEAN-REVERSION-15M", "15m", "mean_reversion", generate_signals_mean_reversion),
    ("V36-MEAN-REVERSION-30M", "30m", "mean_reversion", generate_signals_mean_reversion),

    ("V36-LIQUIDITY-REVERSAL-1H", "1h", "liquidity_reversal", generate_signals_liquidity_reversal),
    ("V36-VOL-EXPANSION-1H",  "1h",  "volatility_expansion", generate_signals_volatility_expansion),

    ("V36-TREND-CONT-1H",     "1h",  "trend_continuation", generate_signals_trend_continuation),
    ("V36-MTF-CONFLUENCE-1H", "1h",  "mtf_confluence", generate_signals_mtf_confluence),

    ("V36-STRUCTURE-BREAKOUT-1H", "1h", "structure_breakout", generate_signals_structure_breakout),
    ("V36-REGIME-HYBRID-1H", "1h",  "regime_adaptive_hybrid", generate_signals_regime_adaptive_hybrid),

    ("V36-VOL-COMPRESSION-1H", "1h", "volatility_compression", generate_signals_volatility_compression),
    ("V36-RELATIVE-STRENGTH-1H", "1h", "relative_strength", generate_signals_relative_strength)
]
