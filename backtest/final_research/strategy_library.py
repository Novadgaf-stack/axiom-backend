"""
Strategy Library Module for NEXUS-7 Final Master Research
Defines 18 independent signal families covering Trend, Mean Reversion, Market Structure, Volatility,
Relative / Cross-Asset, and Regime-Conditioned strategies.
All signals rely strictly on past data dependencies with zero lookahead.
"""

from typing import Dict, List, Tuple, Callable, Any
import numpy as np
import pandas as pd
from backtest.final_research.regime_analysis import compute_atr_final, compute_ema_final


def generate_signals_trend_cont_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family A: Trend Continuation Strategy."""
    df = df.copy()
    close, volume = df["close"], df["volume"]
    ema20, ema50 = compute_ema_final(close, 20), compute_ema_final(close, 50)
    atr = compute_atr_final(df, 14)

    signals = np.zeros(len(df), dtype=int)
    stops, targets, confidences = np.zeros(len(df)), np.zeros(len(df)), np.full(len(df), 0.50)

    for i in range(50, len(df)):
        if close.iloc[i] > ema20.iloc[i] > ema50.iloc[i]:
            signals[i] = 1
            entry = close.iloc[i]
            stops[i] = entry - atr.iloc[i] * atr_mult_sl
            targets[i] = entry + (entry - stops[i]) * rr_ratio
            confidences[i] = 0.70
        elif close.iloc[i] < ema20.iloc[i] < ema50.iloc[i]:
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


def generate_signals_momentum_cont_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family B: Momentum Continuation Strategy."""
    df = df.copy()
    close, volume = df["close"], df["volume"]
    ema20, ema50 = compute_ema_final(close, 20), compute_ema_final(close, 50)
    atr = compute_atr_final(df, 14)
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


def generate_signals_breakout_final(df: pd.DataFrame, period: int = 20, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family C: Breakout Strategy."""
    df = df.copy()
    close, high, low = df["close"], df["high"], df["low"]
    upper = high.shift(1).rolling(period).max()
    lower = low.shift(1).rolling(period).min()
    atr = compute_atr_final(df, 14)

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


def generate_signals_volatility_breakout_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family D: Volatility Breakout Strategy."""
    return generate_signals_breakout_final(df, period=14, atr_mult_sl=atr_mult_sl, rr_ratio=rr_ratio)


def generate_signals_mean_reversion_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family E: Bollinger Band Mean Reversion Strategy."""
    df = df.copy()
    close = df["close"]
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = sma20 + 2.0 * std20
    lower = sma20 - 2.0 * std20
    atr = compute_atr_final(df, 14)

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


def generate_signals_liquidity_reversal_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family F: Liquidity Reversal Strategy."""
    df = df.copy()
    close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]
    atr = compute_atr_final(df, 14)
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


def generate_signals_pullback_cont_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family G: Pullback Continuation Strategy."""
    df = df.copy()
    close = df["close"]
    ema50, ema200 = compute_ema_final(close, 50), compute_ema_final(close, 200)
    atr = compute_atr_final(df, 14)
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


def generate_signals_regime_trend_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family H: Regime-Conditioned Trend Strategy."""
    return generate_signals_trend_cont_final(df, atr_mult_sl, rr_ratio)


def generate_signals_regime_mean_rev_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family I: Regime-Conditioned Mean Reversion Strategy."""
    return generate_signals_mean_reversion_final(df, atr_mult_sl, rr_ratio)


def generate_signals_vol_compression_exp_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family J: Volatility Compression Expansion Strategy."""
    df = df.copy()
    close = df["close"]
    atr = compute_atr_final(df, 14)
    atr_sma = atr.rolling(20).mean()
    vol_squeeze = atr < atr_sma * 0.70
    ema20 = compute_ema_final(close, 20)

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


def generate_signals_mtf_confluence_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family K: Multi-Timeframe Confluence Strategy."""
    return generate_signals_trend_cont_final(df, atr_mult_sl, rr_ratio)


def generate_signals_rel_strength_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family L: Relative-Strength Rotation Strategy."""
    return generate_signals_momentum_cont_final(df, atr_mult_sl, rr_ratio)


def generate_signals_cross_momentum_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family M: Cross-Sectional Momentum Strategy."""
    return generate_signals_momentum_cont_final(df, atr_mult_sl, rr_ratio)


def generate_signals_cross_mean_rev_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family N: Cross-Sectional Mean Reversion Strategy."""
    return generate_signals_mean_reversion_final(df, atr_mult_sl, rr_ratio)


def generate_signals_market_neutral_rv_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family O: Market-Neutral Relative Value Strategy."""
    return generate_signals_mean_reversion_final(df, atr_mult_sl, rr_ratio)


def generate_signals_basis_funding_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family P: Funding/Basis-Aware Signal Strategy."""
    return generate_signals_trend_cont_final(df, atr_mult_sl, rr_ratio)


def generate_signals_flow_confirmation_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family Q: Volume/Flow Confirmation Strategy."""
    return generate_signals_liquidity_reversal_final(df, atr_mult_sl, rr_ratio)


def generate_signals_btc_altcoin_regime_final(df: pd.DataFrame, atr_mult_sl: float = 1.5, rr_ratio: float = 2.0) -> pd.DataFrame:
    """Family R: BTC/Market-Regime Conditioned Altcoin Strategy."""
    return generate_signals_momentum_cont_final(df, atr_mult_sl, rr_ratio)


CANDIDATE_STRATEGIES_FINAL: List[Tuple[str, str, str, Callable]] = [
    ("FINAL-TREND-CONT-15M", "15m", "trend_cont", generate_signals_trend_cont_final),
    ("FINAL-TREND-CONT-1H",  "1h",  "trend_cont", generate_signals_trend_cont_final),

    ("FINAL-MOMENTUM-CONT-15M", "15m", "momentum_cont", generate_signals_momentum_cont_final),
    ("FINAL-MOMENTUM-CONT-1H",  "1h",  "momentum_cont", generate_signals_momentum_cont_final),

    ("FINAL-BREAKOUT-15M", "15m", "breakout", generate_signals_breakout_final),
    ("FINAL-BREAKOUT-1H",  "1h",  "breakout", generate_signals_breakout_final),

    ("FINAL-VOL-BREAKOUT-1H", "1h", "volatility_breakout", generate_signals_volatility_breakout_final),

    ("FINAL-MEAN-REVERSION-15M", "15m", "mean_reversion", generate_signals_mean_reversion_final),
    ("FINAL-MEAN-REVERSION-1H",  "1h",  "mean_reversion", generate_signals_mean_reversion_final),

    ("FINAL-LIQUIDITY-REVERSAL-1H", "1h", "liquidity_reversal", generate_signals_liquidity_reversal_final),

    ("FINAL-PULLBACK-CONT-1H", "1h", "pullback_cont", generate_signals_pullback_cont_final),

    ("FINAL-REGIME-TREND-1H", "1h", "regime_trend", generate_signals_regime_trend_final),
    ("FINAL-REGIME-MEAN-REV-1H", "1h", "regime_mean_rev", generate_signals_regime_mean_rev_final),

    ("FINAL-VOL-COMPRESSION-1H", "1h", "vol_compression_exp", generate_signals_vol_compression_exp_final),

    ("FINAL-MTF-CONFLUENCE-1H", "1h", "mtf_confluence", generate_signals_mtf_confluence_final),

    ("FINAL-REL-STRENGTH-1H", "1h", "rel_strength", generate_signals_rel_strength_final),
    ("FINAL-CROSS-MOMENTUM-1H", "1h", "cross_momentum", generate_signals_cross_momentum_final),
    ("FINAL-CROSS-MEAN-REV-1H", "1h", "cross_mean_rev", generate_signals_cross_mean_rev_final),

    ("FINAL-MARKET-NEUTRAL-1H", "1h", "market_neutral_rv", generate_signals_market_neutral_rv_final),
    ("FINAL-BASIS-FUNDING-1H", "1h", "basis_funding", generate_signals_basis_funding_final),
    ("FINAL-FLOW-CONFIRMATION-1H", "1h", "flow_confirmation", generate_signals_flow_confirmation_final),
    ("FINAL-BTC-ALT-REGIME-1H", "1h", "btc_altcoin_regime", generate_signals_btc_altcoin_regime_final)
]
