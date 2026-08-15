"""
Strategy Library Module for NEXUS-7 Research V32
Contains 9 distinct strategy families across 18 candidate configurations with structural exits.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=1).mean()


def generate_signals_trend_cont(
    df: pd.DataFrame,
    fast_period: int = 10,
    slow_period: int = 30,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """1. Trend Continuation Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(1, len(df_out)):
        if ema_fast.iloc[i] > ema_slow.iloc[i] and ema_fast.iloc[i-1] <= ema_slow.iloc[i-1]:
            signals[i] = 1
            entry_price = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry_price - dist
            tp[i] = entry_price + dist * rr_ratio
            conf[i] = 0.70 + min(0.25, (ema_fast.iloc[i] - ema_slow.iloc[i]) / entry_price * 10.0)

        elif ema_fast.iloc[i] < ema_slow.iloc[i] and ema_fast.iloc[i-1] >= ema_slow.iloc[i-1]:
            signals[i] = -1
            entry_price = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry_price + dist
            tp[i] = entry_price - dist * rr_ratio
            conf[i] = 0.70 + min(0.25, (ema_slow.iloc[i] - ema_fast.iloc[i]) / entry_price * 10.0)

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_breakout_vol(
    df: pd.DataFrame,
    lookback: int = 20,
    vol_mult: float = 1.2,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """2. Breakout & Volatility Expansion Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    high = df_out["high"]
    low = df_out["low"]
    volume = df_out["volume"]

    rolling_high = high.rolling(lookback).max().shift(1)
    rolling_low = low.rolling(lookback).min().shift(1)
    vol_sma = volume.rolling(lookback).mean()
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(lookback, len(df_out)):
        if close.iloc[i] > rolling_high.iloc[i] and volume.iloc[i] > vol_sma.iloc[i] * vol_mult:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.75 + min(0.20, (volume.iloc[i] / vol_sma.iloc[i] - 1.0) * 0.1)

        elif close.iloc[i] < rolling_low.iloc[i] and volume.iloc[i] > vol_sma.iloc[i] * vol_mult:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.75 + min(0.20, (volume.iloc[i] / vol_sma.iloc[i] - 1.0) * 0.1)

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_pullback_cont(
    df: pd.DataFrame,
    trend_period: int = 50,
    rsi_period: int = 14,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 1.8
) -> pd.DataFrame:
    """3. Pullback Continuation Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    ema_trend = close.ewm(span=trend_period, adjust=False).mean()

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / (loss + 1e-8)
    rsi = 100 - (100 / (1 + rs))

    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(trend_period, len(df_out)):
        if close.iloc[i] > ema_trend.iloc[i] and rsi.iloc[i] < 42.0 and rsi.iloc[i-1] >= 42.0:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.72

        elif close.iloc[i] < ema_trend.iloc[i] and rsi.iloc[i] > 58.0 and rsi.iloc[i-1] <= 58.0:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.72

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_liquidity_reversal(
    df: pd.DataFrame,
    lookback: int = 24,
    atr_mult_sl: float = 1.2,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """4. Liquidity Sweep & Structure Reversal Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    high = df_out["high"]
    low = df_out["low"]

    recent_high = high.rolling(lookback).max().shift(1)
    recent_low = low.rolling(lookback).min().shift(1)
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(lookback, len(df_out)):
        if low.iloc[i] < recent_low.iloc[i] and close.iloc[i] > recent_low.iloc[i]:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.80

        elif high.iloc[i] > recent_high.iloc[i] and close.iloc[i] < recent_high.iloc[i]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.80

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_regime_mom(
    df: pd.DataFrame,
    mom_period: int = 14,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """5. Regime-Aware Momentum Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    mom = close.pct_change(mom_period)
    ema_200 = close.ewm(span=200, adjust=False).mean()
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(200, len(df_out)):
        if close.iloc[i] > ema_200.iloc[i] and mom.iloc[i] > 0.03 and mom.iloc[i-1] <= 0.03:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.76

        elif close.iloc[i] < ema_200.iloc[i] and mom.iloc[i] < -0.03 and mom.iloc[i-1] >= -0.03:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.76

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_mean_reversion(
    df: pd.DataFrame,
    bb_period: int = 20,
    bb_std: float = 2.0,
    atr_mult_sl: float = 1.2,
    rr_ratio: float = 1.5
) -> pd.DataFrame:
    """6. Mean Reversion Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    sma = close.rolling(bb_period).mean()
    std = close.rolling(bb_period).std()
    upper = sma + bb_std * std
    lower = sma - bb_std * std
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(bb_period, len(df_out)):
        if close.iloc[i] < lower.iloc[i] and close.iloc[i-1] >= lower.iloc[i-1]:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.70

        elif close.iloc[i] > upper.iloc[i] and close.iloc[i-1] <= upper.iloc[i-1]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.70

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_momentum_cont(
    df: pd.DataFrame,
    period: int = 12,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """7. Momentum Continuation Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    roc = close.pct_change(period)
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(period, len(df_out)):
        if roc.iloc[i] > 0.025 and roc.iloc[i-1] <= 0.025:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.74

        elif roc.iloc[i] < -0.025 and roc.iloc[i-1] >= -0.025:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.74

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_mtf_confluence(
    df: pd.DataFrame,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """8. Multi-Timeframe (MTF) Confluence Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(200, len(df_out)):
        if close.iloc[i] > ema200.iloc[i] and ema20.iloc[i] > ema50.iloc[i] and ema20.iloc[i-1] <= ema50.iloc[i-1]:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.82

        elif close.iloc[i] < ema200.iloc[i] and ema20.iloc[i] < ema50.iloc[i] and ema20.iloc[i-1] >= ema50.iloc[i-1]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.82

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_vol_comp_exp(
    df: pd.DataFrame,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """9. Volatility Compression -> Expansion Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    atr = _compute_atr(df_out, period=14)
    atr_sma = atr.rolling(30).mean()
    volume = df_out["volume"]
    vol_sma = volume.rolling(20).mean()

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(30, len(df_out)):
        is_compressed = atr.iloc[i-1] < atr_sma.iloc[i-1] * 0.8
        is_expanding = atr.iloc[i] > atr_sma.iloc[i] * 1.1 and volume.iloc[i] > vol_sma.iloc[i] * 1.2

        if is_compressed and is_expanding:
            if close.iloc[i] > close.iloc[i-1]:
                signals[i] = 1
                entry = close.iloc[i]
                dist = atr.iloc[i] * atr_mult_sl
                sl[i] = entry - dist
                tp[i] = entry + dist * rr_ratio
                conf[i] = 0.78
            else:
                signals[i] = -1
                entry = close.iloc[i]
                dist = atr.iloc[i] * atr_mult_sl
                sl[i] = entry + dist
                tp[i] = entry - dist * rr_ratio
                conf[i] = 0.78

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_adaptive_hybrid(
    df: pd.DataFrame,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """10. Regime-Aware Adaptive Hybrid Strategy."""
    df_out = df.copy()
    df_trend = generate_signals_trend_cont(df, atr_mult_sl=atr_mult_sl, rr_ratio=rr_ratio)
    df_break = generate_signals_breakout_vol(df, atr_mult_sl=atr_mult_sl, rr_ratio=rr_ratio)

    close = df["close"]
    ema_200 = close.ewm(span=200, adjust=False).mean()
    atr = _compute_atr(df, period=14)

    signals = np.zeros(len(df), dtype=int)
    sl = np.zeros(len(df))
    tp = np.zeros(len(df))
    conf = np.zeros(len(df))

    for i in range(200, len(df)):
        # If in strong trend, use trend continuation; otherwise breakout
        is_trending = abs(close.iloc[i] - ema_200.iloc[i]) / close.iloc[i] > 0.02
        if is_trending:
            signals[i] = df_trend["signal"].iloc[i]
            sl[i] = df_trend["stop_loss"].iloc[i]
            tp[i] = df_trend["take_profit"].iloc[i]
            conf[i] = df_trend["confidence"].iloc[i]
        else:
            signals[i] = df_break["signal"].iloc[i]
            sl[i] = df_break["stop_loss"].iloc[i]
            tp[i] = df_break["take_profit"].iloc[i]
            conf[i] = df_break["confidence"].iloc[i]

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


CANDIDATE_STRATEGIES = [
    ("V32-TREND-CONT-30M", "30m", "trend_cont", generate_signals_trend_cont),
    ("V32-TREND-CONT-1H", "1h", "trend_cont", generate_signals_trend_cont),
    ("V32-BREAKOUT-VOL-30M", "30m", "breakout_vol", generate_signals_breakout_vol),
    ("V32-BREAKOUT-VOL-1H", "1h", "breakout_vol", generate_signals_breakout_vol),
    ("V32-PULLBACK-CONT-30M", "30m", "pullback_cont", generate_signals_pullback_cont),
    ("V32-PULLBACK-CONT-15M", "15m", "pullback_cont", generate_signals_pullback_cont),
    ("V32-LIQUIDITY-REVERSAL-1H", "1h", "liquidity_reversal", generate_signals_liquidity_reversal),
    ("V32-LIQUIDITY-REVERSAL-15M", "15m", "liquidity_reversal", generate_signals_liquidity_reversal),
    ("V32-REGIME-MOM-30M", "30m", "regime_mom", generate_signals_regime_mom),
    ("V32-REGIME-MOM-1H", "1h", "regime_mom", generate_signals_regime_mom),
    ("V32-MEAN-REVERSION-30M", "30m", "mean_reversion", generate_signals_mean_reversion),
    ("V32-MEAN-REVERSION-15M", "15m", "mean_reversion", generate_signals_mean_reversion),
    ("V32-MOMENTUM-CONT-30M", "30m", "momentum_cont", generate_signals_momentum_cont),
    ("V32-MTF-CONFLUENCE-30M", "30m", "mtf_confluence", generate_signals_mtf_confluence),
    ("V32-MTF-CONFLUENCE-1H", "1h", "mtf_confluence", generate_signals_mtf_confluence),
    ("V32-VOL-COMP-EXP-4H", "4h", "vol_comp_exp", generate_signals_vol_comp_exp),
    ("V32-VOL-COMP-EXP-1H", "1h", "vol_comp_exp", generate_signals_vol_comp_exp),
    ("V32-ADAPTIVE-HYBRID-4H", "4h", "adaptive_hybrid", generate_signals_adaptive_hybrid),
    ("V32-ADAPTIVE-HYBRID-1H", "1h", "adaptive_hybrid", generate_signals_adaptive_hybrid),
]
