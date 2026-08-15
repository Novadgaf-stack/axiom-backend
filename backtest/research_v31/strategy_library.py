"""
NEXUS-7 Research V31 — Strategy Library Module
Implements 9 distinct strategy families across 18 candidate configurations with
structural exit research (ATR stops, trailing stops, fixed R targets) and parameter scaling hooks.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Computes technical indicators required for strategy generation."""
    data = df.copy()

    # EMAs
    data["ema_9"] = data["close"].ewm(span=9, adjust=False).mean()
    data["ema_21"] = data["close"].ewm(span=21, adjust=False).mean()
    data["ema_50"] = data["close"].ewm(span=50, adjust=False).mean()
    data["ema_200"] = data["close"].ewm(span=200, adjust=False).mean()

    # ATR (14)
    tr1 = data["high"] - data["low"]
    tr2 = (data["high"] - data["close"].shift(1)).abs()
    tr3 = (data["low"] - data["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    data["atr_14"] = tr.rolling(window=14, min_periods=1).mean()

    # Bollinger Bands (20, 2)
    data["bb_mid"] = data["close"].rolling(window=20, min_periods=1).mean()
    bb_std = data["close"].rolling(window=20, min_periods=1).std().fillna(0)
    data["bb_upper"] = data["bb_mid"] + 2.0 * bb_std
    data["bb_lower"] = data["bb_mid"] - 2.0 * bb_std
    data["bb_width"] = (data["bb_upper"] - data["bb_lower"]) / (data["bb_mid"] + 1e-8)

    # RSI (14)
    delta = data["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss + 1e-8)
    data["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))

    # Volume Z-score (20)
    vol_mean = data["volume"].rolling(window=20, min_periods=1).mean()
    vol_std = data["volume"].rolling(window=20, min_periods=1).std().fillna(1.0)
    data["volume_z"] = (data["volume"] - vol_mean) / (vol_std + 1e-8)

    # Donchian High / Low (20)
    data["donchian_high_20"] = data["high"].rolling(window=20, min_periods=1).max().shift(1)
    data["donchian_low_20"] = data["low"].rolling(window=20, min_periods=1).min().shift(1)

    # ADX Proxy
    up_move = data["high"].diff()
    down_move = -data["low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100 * (pd.Series(plus_dm).rolling(14, min_periods=1).mean() / (data["atr_14"] + 1e-8))
    minus_di = 100 * (pd.Series(minus_dm).rolling(14, min_periods=1).mean() / (data["atr_14"] + 1e-8))
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-8)
    data["adx_14"] = dx.rolling(14, min_periods=1).mean()

    return data


# --- Family 1: Trend Continuation ---
def generate_signals_trend_cont(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.5 * param_mult; rr = 2.0

    for i in range(50, n):
        close = data["close"].iloc[i]; ema9 = data["ema_9"].iloc[i]; ema21 = data["ema_21"].iloc[i]
        ema200 = data["ema_200"].iloc[i]; atr = data["atr_14"].iloc[i]; vol_z = data["volume_z"].iloc[i]

        if ema9 > ema21 and close > ema200 and vol_z > (0.6 / param_mult):
            signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.85
        elif ema9 < ema21 and close < ema200 and vol_z > (0.6 / param_mult):
            signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.85

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 2: Breakout + Volatility Expansion ---
def generate_signals_breakout_vol(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.4 * param_mult; rr = 2.2

    for i in range(20, n):
        close = data["close"].iloc[i]; donch_h = data["donchian_high_20"].iloc[i]
        donch_l = data["donchian_low_20"].iloc[i]; vol_z = data["volume_z"].iloc[i]; atr = data["atr_14"].iloc[i]

        if close > donch_h and vol_z > (0.9 / param_mult):
            signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.80
        elif close < donch_l and vol_z > (0.9 / param_mult):
            signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.80

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 3: Pullback Continuation ---
def generate_signals_pullback_cont(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.6 * param_mult; rr = 1.8

    for i in range(50, n):
        close = data["close"].iloc[i]; ema50 = data["ema_50"].iloc[i]; ema200 = data["ema_200"].iloc[i]
        rsi = data["rsi_14"].iloc[i]; atr = data["atr_14"].iloc[i]

        if ema50 > ema200 and rsi < (40.0 * param_mult):
            signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.75
        elif ema50 < ema200 and rsi > (60.0 / param_mult):
            signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.75

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 4: Liquidity Sweep / Structure Reversal ---
def generate_signals_liquidity_reversal(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    rr = 2.0

    for i in range(20, n):
        low_i = data["low"].iloc[i]; high_i = data["high"].iloc[i]; close_i = data["close"].iloc[i]
        donch_l = data["donchian_low_20"].iloc[i]; donch_h = data["donchian_high_20"].iloc[i]
        vol_z = data["volume_z"].iloc[i]; atr = data["atr_14"].iloc[i]

        sweep_low = (low_i < donch_l) and (close_i > donch_l) and (vol_z > (1.1 / param_mult))
        sweep_high = (high_i > donch_h) and (close_i < donch_h) and (vol_z > (1.1 / param_mult))

        if sweep_low:
            signals[i] = 1; sl[i] = low_i - atr * 0.2; tp[i] = close_i + (close_i - sl[i]) * rr; conf[i] = 0.78
        elif sweep_high:
            signals[i] = -1; sl[i] = high_i + atr * 0.2; tp[i] = close_i - (sl[i] - close_i) * rr; conf[i] = 0.78

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 5: Regime-Aware Momentum ---
def generate_signals_regime_mom(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.5 * param_mult; rr = 2.0

    for i in range(50, n):
        close = data["close"].iloc[i]; adx = data["adx_14"].iloc[i]; ema9 = data["ema_9"].iloc[i]
        ema21 = data["ema_21"].iloc[i]; atr = data["atr_14"].iloc[i]

        if adx > (25.0 / param_mult):
            if ema9 > ema21:
                signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.82
            elif ema9 < ema21:
                signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.82

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 6: Mean Reversion ---
def generate_signals_mean_reversion(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.2 * param_mult; rr = 1.5

    for i in range(20, n):
        close = data["close"].iloc[i]; bb_low = data["bb_lower"].iloc[i]; bb_high = data["bb_upper"].iloc[i]
        adx = data["adx_14"].iloc[i]; atr = data["atr_14"].iloc[i]

        if adx < (22.0 / param_mult):
            if close <= bb_low:
                signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.70
            elif close >= bb_high:
                signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.70

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 7: Multi-Timeframe Confluence ---
def generate_signals_mtf_confluence(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.8 * param_mult; rr = 2.5

    for i in range(50, n):
        close = data["close"].iloc[i]; ema9 = data["ema_9"].iloc[i]; ema21 = data["ema_21"].iloc[i]
        ema50 = data["ema_50"].iloc[i]; adx = data["adx_14"].iloc[i]; vol_z = data["volume_z"].iloc[i]; atr = data["atr_14"].iloc[i]

        if (ema9 > ema21 > ema50) and adx > (24.0 / param_mult) and vol_z > (0.5 / param_mult):
            signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.86
        elif (ema9 < ema21 < ema50) and adx > (24.0 / param_mult) and vol_z > (0.5 / param_mult):
            signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.86

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 8: Volatility Compression -> Expansion ---
def generate_signals_vol_comp_exp(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.5 * param_mult; rr = 2.0

    for i in range(21, n):
        close = data["close"].iloc[i]; bb_w = data["bb_width"].iloc[i]; bb_w_prev = data["bb_width"].iloc[i-1]
        atr = data["atr_14"].iloc[i]

        expanding = bb_w > (bb_w_prev * 1.12 * param_mult)
        if expanding:
            if close > data["bb_mid"].iloc[i]:
                signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.72
            elif close < data["bb_mid"].iloc[i]:
                signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.72

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Family 9: Adaptive Hybrid Strategy ---
def generate_signals_adaptive_hybrid(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)
    signals, sl, tp, conf = np.zeros(n, dtype=int), np.zeros(n), np.zeros(n), np.zeros(n)
    atr_sl_mult = 1.6 * param_mult; rr = 2.2

    for i in range(50, n):
        close = data["close"].iloc[i]; adx = data["adx_14"].iloc[i]; ema9 = data["ema_9"].iloc[i]
        ema21 = data["ema_21"].iloc[i]; vol_z = data["volume_z"].iloc[i]; atr = data["atr_14"].iloc[i]

        # Trending regime -> trend entry
        if adx > (25.0 / param_mult) and vol_z > (0.7 / param_mult):
            if ema9 > ema21:
                signals[i] = 1; sl[i] = close - atr * atr_sl_mult; tp[i] = close + atr * atr_sl_mult * rr; conf[i] = 0.88
            elif ema9 < ema21:
                signals[i] = -1; sl[i] = close + atr * atr_sl_mult; tp[i] = close - atr * atr_sl_mult * rr; conf[i] = 0.88

    data["signal"], data["stop_loss"], data["take_profit"], data["confidence"] = signals, sl, tp, conf
    return data


# --- Candidate Registry (18 Candidate Configurations) ---
CANDIDATE_STRATEGIES = {
    "V31-TREND-CONT-30M": {"family": "trend_cont", "timeframe": "30m", "func": generate_signals_trend_cont},
    "V31-TREND-CONT-1H": {"family": "trend_cont", "timeframe": "1h", "func": generate_signals_trend_cont},
    "V31-BREAKOUT-VOL-30M": {"family": "breakout_vol", "timeframe": "30m", "func": generate_signals_breakout_vol},
    "V31-BREAKOUT-VOL-1H": {"family": "breakout_vol", "timeframe": "1h", "func": generate_signals_breakout_vol},
    "V31-PULLBACK-CONT-15M": {"family": "pullback_cont", "timeframe": "15m", "func": generate_signals_pullback_cont},
    "V31-PULLBACK-CONT-30M": {"family": "pullback_cont", "timeframe": "30m", "func": generate_signals_pullback_cont},
    "V31-LIQUIDITY-REVERSAL-15M": {"family": "liquidity_reversal", "timeframe": "15m", "func": generate_signals_liquidity_reversal},
    "V31-LIQUIDITY-REVERSAL-1H": {"family": "liquidity_reversal", "timeframe": "1h", "func": generate_signals_liquidity_reversal},
    "V31-REGIME-MOM-30M": {"family": "regime_mom", "timeframe": "30m", "func": generate_signals_regime_mom},
    "V31-REGIME-MOM-1H": {"family": "regime_mom", "timeframe": "1h", "func": generate_signals_regime_mom},
    "V31-MEAN-REVERSION-15M": {"family": "mean_reversion", "timeframe": "15m", "func": generate_signals_mean_reversion},
    "V31-MEAN-REVERSION-30M": {"family": "mean_reversion", "timeframe": "30m", "func": generate_signals_mean_reversion},
    "V31-MTF-CONFLUENCE-30M": {"family": "mtf_confluence", "timeframe": "30m", "func": generate_signals_mtf_confluence},
    "V31-MTF-CONFLUENCE-1H": {"family": "mtf_confluence", "timeframe": "1h", "func": generate_signals_mtf_confluence},
    "V31-VOL-COMP-EXP-1H": {"family": "vol_comp_exp", "timeframe": "1h", "func": generate_signals_vol_comp_exp},
    "V31-VOL-COMP-EXP-4H": {"family": "vol_comp_exp", "timeframe": "4h", "func": generate_signals_vol_comp_exp},
    "V31-ADAPTIVE-HYBRID-1H": {"family": "adaptive_hybrid", "timeframe": "1h", "func": generate_signals_adaptive_hybrid},
    "V31-ADAPTIVE-HYBRID-4H": {"family": "adaptive_hybrid", "timeframe": "4h", "func": generate_signals_adaptive_hybrid},
}
