"""
Strategy Library Module for NEXUS-7 Research V34
Contains 11 distinct strategy families across 22 candidate configurations with structural exits.
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
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.75 + min(0.20, (ema_fast.iloc[i] - ema_slow.iloc[i]) / entry * 10.0)

        elif ema_fast.iloc[i] < ema_slow.iloc[i] and ema_fast.iloc[i-1] >= ema_slow.iloc[i-1]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.75 + min(0.20, (ema_slow.iloc[i] - ema_fast.iloc[i]) / entry * 10.0)

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


def generate_signals_breakout(
    df: pd.DataFrame,
    lookback: int = 20,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """2. Breakout Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    high = df_out["high"]
    low = df_out["low"]

    rolling_high = high.rolling(lookback).max().shift(1)
    rolling_low = low.rolling(lookback).min().shift(1)
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(lookback + 1, len(df_out)):
        if close.iloc[i] > rolling_high.iloc[i]:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.78

        elif close.iloc[i] < rolling_low.iloc[i]:
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


def generate_signals_vol_comp_exp(
    df: pd.DataFrame,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """3. Volatility Compression -> Expansion Strategy."""
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
                conf[i] = 0.82
            else:
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


def generate_signals_momentum_cont(
    df: pd.DataFrame,
    rsi_period: int = 14,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """4. Momentum Continuation Strategy."""
    df_out = df.copy()
    close = df_out["close"]
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

    for i in range(rsi_period, len(df_out)):
        if rsi.iloc[i-1] <= 50.0 and rsi.iloc[i] > 50.0:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.74

        elif rsi.iloc[i-1] >= 50.0 and rsi.iloc[i] < 50.0:
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


def generate_signals_mean_reversion(
    df: pd.DataFrame,
    bb_period: int = 20,
    bb_std: float = 2.0,
    atr_mult_sl: float = 1.2,
    rr_ratio: float = 1.5
) -> pd.DataFrame:
    """5. Mean Reversion Strategy."""
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
            conf[i] = 0.72

        elif close.iloc[i] > upper.iloc[i] and close.iloc[i-1] <= upper.iloc[i-1]:
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


def generate_signals_liquidity_sweep(
    df: pd.DataFrame,
    lookback: int = 20,
    atr_mult_sl: float = 1.2,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """6. Liquidity Sweep Strategy."""
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
            conf[i] = 0.81

        elif high.iloc[i] > recent_high.iloc[i] and close.iloc[i] < recent_high.iloc[i]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.81

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
    """7. Liquidity Reversal Strategy."""
    df_out = generate_signals_liquidity_sweep(df, lookback=lookback, atr_mult_sl=atr_mult_sl, rr_ratio=rr_ratio)
    return df_out


def generate_signals_market_structure(
    df: pd.DataFrame,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """8. Market Structure Reversal Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    high = df_out["high"]
    low = df_out["low"]
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(5, len(df_out)):
        # Higher High + Higher Low reversal confirmation
        if low.iloc[i-2] < low.iloc[i-4] and close.iloc[i] > high.iloc[i-2]:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.79

        # Lower Low + Lower High reversal confirmation
        elif high.iloc[i-2] > high.iloc[i-4] and close.iloc[i] < low.iloc[i-2]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.79

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
    """9. Multi-Timeframe (MTF) Confluence Strategy."""
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
            conf[i] = 0.83

        elif close.iloc[i] < ema200.iloc[i] and ema20.iloc[i] < ema50.iloc[i] and ema20.iloc[i-1] >= ema50.iloc[i-1]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.83

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
    """10. Adaptive Hybrid Strategy."""
    df_out = df.copy()
    df_trend = generate_signals_trend_cont(df, atr_mult_sl=atr_mult_sl, rr_ratio=rr_ratio)
    df_break = generate_signals_breakout(df, atr_mult_sl=atr_mult_sl, rr_ratio=rr_ratio)

    close = df["close"]
    ema_200 = close.ewm(span=200, adjust=False).mean()

    signals = np.zeros(len(df), dtype=int)
    sl = np.zeros(len(df))
    tp = np.zeros(len(df))
    conf = np.zeros(len(df))

    for i in range(200, len(df)):
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


def generate_signals_regime_aware(
    df: pd.DataFrame,
    trend_period: int = 100,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 2.0
) -> pd.DataFrame:
    """11. Market Regime-Aware Strategy."""
    df_out = df.copy()
    close = df_out["close"]
    ema_trend = close.ewm(span=trend_period, adjust=False).mean()
    atr = _compute_atr(df_out, period=14)

    signals = np.zeros(len(df_out), dtype=int)
    sl = np.zeros(len(df_out))
    tp = np.zeros(len(df_out))
    conf = np.zeros(len(df_out))

    for i in range(trend_period, len(df_out)):
        trend_dist = (close.iloc[i] - ema_trend.iloc[i]) / ema_trend.iloc[i]
        if trend_dist > 0.02 and close.iloc[i] > close.iloc[i-1]:
            signals[i] = 1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry - dist
            tp[i] = entry + dist * rr_ratio
            conf[i] = 0.84

        elif trend_dist < -0.02 and close.iloc[i] < close.iloc[i-1]:
            signals[i] = -1
            entry = close.iloc[i]
            dist = atr.iloc[i] * atr_mult_sl
            sl[i] = entry + dist
            tp[i] = entry - dist * rr_ratio
            conf[i] = 0.84

    df_out["signal"] = signals
    df_out["stop_loss"] = sl
    df_out["take_profit"] = tp
    df_out["confidence"] = conf
    return df_out


CANDIDATE_STRATEGIES = [
    ("V34-TREND-CONT-30M", "30m", "trend_cont", generate_signals_trend_cont),
    ("V34-TREND-CONT-1H", "1h", "trend_cont", generate_signals_trend_cont),
    ("V34-BREAKOUT-30M", "30m", "breakout", generate_signals_breakout),
    ("V34-BREAKOUT-1H", "1h", "breakout", generate_signals_breakout),
    ("V34-VOL-COMP-EXP-1H", "1h", "vol_comp_exp", generate_signals_vol_comp_exp),
    ("V34-MOMENTUM-CONT-30M", "30m", "momentum_cont", generate_signals_momentum_cont),
    ("V34-MEAN-REVERSION-30M", "30m", "mean_reversion", generate_signals_mean_reversion),
    ("V34-MEAN-REVERSION-15M", "15m", "mean_reversion", generate_signals_mean_reversion),
    ("V34-LIQUIDITY-SWEEP-1H", "1h", "liquidity_sweep", generate_signals_liquidity_sweep),
    ("V34-LIQUIDITY-REVERSAL-1H", "1h", "liquidity_reversal", generate_signals_liquidity_reversal),
    ("V34-MARKET-STRUCTURE-1H", "1h", "market_structure", generate_signals_market_structure),
    ("V34-MTF-CONFLUENCE-30M", "30m", "mtf_confluence", generate_signals_mtf_confluence),
    ("V34-MTF-CONFLUENCE-1H", "1h", "mtf_confluence", generate_signals_mtf_confluence),
    ("V34-ADAPTIVE-HYBRID-4H", "4h", "adaptive_hybrid", generate_signals_adaptive_hybrid),
    ("V34-ADAPTIVE-HYBRID-1H", "1h", "adaptive_hybrid", generate_signals_adaptive_hybrid),
    ("V34-REGIME-AWARE-1H", "1h", "regime_aware", generate_signals_regime_aware),
]
