"""
NEXUS-7 Research V30 — Strategy Library Module
Implements 6 distinct strategy families across 14 candidate configurations with
indicator calculations and parameter scaling hooks (param_mult) for neighboring parameter testing.
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


# --- Family A: Regime-Aware Trend Continuation ---
def generate_signals_regime_trend(
    df: pd.DataFrame,
    param_mult: float = 1.0
) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)

    signals = np.zeros(n, dtype=int)
    stop_loss = np.zeros(n)
    take_profit = np.zeros(n)
    confidence = np.zeros(n)

    atr_mult_sl = 1.5 * param_mult
    rr_ratio = 2.0

    for i in range(50, n):
        close = data["close"].iloc[i]
        ema_9 = data["ema_9"].iloc[i]
        ema_21 = data["ema_21"].iloc[i]
        ema_200 = data["ema_200"].iloc[i]
        adx = data["adx_14"].iloc[i]
        vol_z = data["volume_z"].iloc[i]
        atr = data["atr_14"].iloc[i]

        # Strong directional regime
        regime_bull = (ema_9 > ema_21) and (close > ema_200) and (adx > (24.0 / param_mult))
        regime_bear = (ema_9 < ema_21) and (close < ema_200) and (adx > (24.0 / param_mult))

        if regime_bull and vol_z > (0.6 / param_mult):
            signals[i] = 1
            stop_loss[i] = close - atr * atr_mult_sl
            take_profit[i] = close + atr * atr_mult_sl * rr_ratio
            confidence[i] = min(0.92, 0.65 + vol_z * 0.1)
        elif regime_bear and vol_z > (0.6 / param_mult):
            signals[i] = -1
            stop_loss[i] = close + atr * atr_mult_sl
            take_profit[i] = close - atr * atr_mult_sl * rr_ratio
            confidence[i] = min(0.92, 0.65 + vol_z * 0.1)

    data["signal"] = signals
    data["stop_loss"] = stop_loss
    data["take_profit"] = take_profit
    data["confidence"] = confidence
    return data


# --- Family B: Breakout + Volatility Confirmation ---
def generate_signals_breakout_vol(
    df: pd.DataFrame,
    param_mult: float = 1.0
) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)

    signals = np.zeros(n, dtype=int)
    stop_loss = np.zeros(n)
    take_profit = np.zeros(n)
    confidence = np.zeros(n)

    atr_mult_sl = 1.4 * param_mult
    rr_ratio = 2.2

    for i in range(20, n):
        close = data["close"].iloc[i]
        donch_h = data["donchian_high_20"].iloc[i]
        donch_l = data["donchian_low_20"].iloc[i]
        vol_z = data["volume_z"].iloc[i]
        atr = data["atr_14"].iloc[i]

        if close > donch_h and vol_z > (0.9 / param_mult):
            signals[i] = 1
            stop_loss[i] = close - atr * atr_mult_sl
            take_profit[i] = close + atr * atr_mult_sl * rr_ratio
            confidence[i] = 0.80
        elif close < donch_l and vol_z > (0.9 / param_mult):
            signals[i] = -1
            stop_loss[i] = close + atr * atr_mult_sl
            take_profit[i] = close - atr * atr_mult_sl * rr_ratio
            confidence[i] = 0.80

    data["signal"] = signals
    data["stop_loss"] = stop_loss
    data["take_profit"] = take_profit
    data["confidence"] = confidence
    return data


# --- Family C: Pullback Continuation ---
def generate_signals_pullback_cont(
    df: pd.DataFrame,
    param_mult: float = 1.0
) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)

    signals = np.zeros(n, dtype=int)
    stop_loss = np.zeros(n)
    take_profit = np.zeros(n)
    confidence = np.zeros(n)

    atr_mult_sl = 1.6 * param_mult
    rr_ratio = 1.8

    for i in range(50, n):
        close = data["close"].iloc[i]
        ema_50 = data["ema_50"].iloc[i]
        ema_200 = data["ema_200"].iloc[i]
        rsi = data["rsi_14"].iloc[i]
        atr = data["atr_14"].iloc[i]

        uptrend = ema_50 > ema_200
        downtrend = ema_50 < ema_200

        if uptrend and rsi < (40.0 * param_mult):
            signals[i] = 1
            stop_loss[i] = close - atr * atr_mult_sl
            take_profit[i] = close + atr * atr_mult_sl * rr_ratio
            confidence[i] = 0.75
        elif downtrend and rsi > (60.0 / param_mult):
            signals[i] = -1
            stop_loss[i] = close + atr * atr_mult_sl
            take_profit[i] = close - atr * atr_mult_sl * rr_ratio
            confidence[i] = 0.75

    data["signal"] = signals
    data["stop_loss"] = stop_loss
    data["take_profit"] = take_profit
    data["confidence"] = confidence
    return data


# --- Family D: Liquidity / Structure Reversal ---
def generate_signals_liquidity_reversal(
    df: pd.DataFrame,
    param_mult: float = 1.0
) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)

    signals = np.zeros(n, dtype=int)
    stop_loss = np.zeros(n)
    take_profit = np.zeros(n)
    confidence = np.zeros(n)

    atr_mult_sl = 1.3 * param_mult
    rr_ratio = 2.0

    for i in range(20, n):
        low_i = data["low"].iloc[i]
        high_i = data["high"].iloc[i]
        close_i = data["close"].iloc[i]
        donch_l = data["donchian_low_20"].iloc[i]
        donch_h = data["donchian_high_20"].iloc[i]
        vol_z = data["volume_z"].iloc[i]
        atr = data["atr_14"].iloc[i]

        sweep_low = (low_i < donch_l) and (close_i > donch_l) and (vol_z > (1.1 / param_mult))
        sweep_high = (high_i > donch_h) and (close_i < donch_h) and (vol_z > (1.1 / param_mult))

        if sweep_low:
            signals[i] = 1
            stop_loss[i] = low_i - atr * 0.2
            take_profit[i] = close_i + (close_i - stop_loss[i]) * rr_ratio
            confidence[i] = 0.78
        elif sweep_high:
            signals[i] = -1
            stop_loss[i] = high_i + atr * 0.2
            take_profit[i] = close_i - (stop_loss[i] - close_i) * rr_ratio
            confidence[i] = 0.78

    data["signal"] = signals
    data["stop_loss"] = stop_loss
    data["take_profit"] = take_profit
    data["confidence"] = confidence
    return data


# --- Family E: Multi-Timeframe Confluence ---
def generate_signals_mtf_confluence(
    df: pd.DataFrame,
    param_mult: float = 1.0
) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)

    signals = np.zeros(n, dtype=int)
    stop_loss = np.zeros(n)
    take_profit = np.zeros(n)
    confidence = np.zeros(n)

    atr_mult_sl = 1.8 * param_mult
    rr_ratio = 2.5

    for i in range(50, n):
        close = data["close"].iloc[i]
        ema_9 = data["ema_9"].iloc[i]
        ema_21 = data["ema_21"].iloc[i]
        ema_50 = data["ema_50"].iloc[i]
        adx = data["adx_14"].iloc[i]
        vol_z = data["volume_z"].iloc[i]
        atr = data["atr_14"].iloc[i]

        trend_bull = (ema_9 > ema_21) and (ema_21 > ema_50)
        trend_bear = (ema_9 < ema_21) and (ema_21 < ema_50)
        high_adx = adx > (25.0 / param_mult)

        if trend_bull and high_adx and vol_z > (0.5 / param_mult):
            signals[i] = 1
            stop_loss[i] = close - atr * atr_mult_sl
            take_profit[i] = close + atr * atr_mult_sl * rr_ratio
            confidence[i] = 0.85
        elif trend_bear and high_adx and vol_z > (0.5 / param_mult):
            signals[i] = -1
            stop_loss[i] = close + atr * atr_mult_sl
            take_profit[i] = close - atr * atr_mult_sl * rr_ratio
            confidence[i] = 0.85

    data["signal"] = signals
    data["stop_loss"] = stop_loss
    data["take_profit"] = take_profit
    data["confidence"] = confidence
    return data


# --- Family F: Volatility-Regime Adaptive Strategy ---
def generate_signals_vol_adaptive(
    df: pd.DataFrame,
    param_mult: float = 1.0
) -> pd.DataFrame:
    data = compute_indicators(df)
    n = len(data)

    signals = np.zeros(n, dtype=int)
    stop_loss = np.zeros(n)
    take_profit = np.zeros(n)
    confidence = np.zeros(n)

    atr_mult_sl = 1.5 * param_mult
    rr_ratio = 2.0

    for i in range(21, n):
        close = data["close"].iloc[i]
        bb_w = data["bb_width"].iloc[i]
        bb_w_prev = data["bb_width"].iloc[i-1]
        adx = data["adx_14"].iloc[i]
        atr = data["atr_14"].iloc[i]

        expanding_vol = bb_w > (bb_w_prev * 1.12 * param_mult)
        ranging = adx < (22.0 / param_mult)

        if expanding_vol:
            if close > data["bb_mid"].iloc[i]:
                signals[i] = 1
                stop_loss[i] = close - atr * atr_mult_sl
                take_profit[i] = close + atr * atr_mult_sl * rr_ratio
                confidence[i] = 0.72
            elif close < data["bb_mid"].iloc[i]:
                signals[i] = -1
                stop_loss[i] = close + atr * atr_mult_sl
                take_profit[i] = close - atr * atr_mult_sl * rr_ratio
                confidence[i] = 0.72

    data["signal"] = signals
    data["stop_loss"] = stop_loss
    data["take_profit"] = take_profit
    data["confidence"] = confidence
    return data


# --- Candidates Registry (14 Candidate Configurations) ---
CANDIDATE_STRATEGIES = {
    "V30-REGIME-TREND-30M": {"family": "regime_trend", "timeframe": "30m", "func": generate_signals_regime_trend},
    "V30-REGIME-TREND-1H": {"family": "regime_trend", "timeframe": "1h", "func": generate_signals_regime_trend},
    "V30-BREAKOUT-VOL-30M": {"family": "breakout_vol", "timeframe": "30m", "func": generate_signals_breakout_vol},
    "V30-BREAKOUT-VOL-1H": {"family": "breakout_vol", "timeframe": "1h", "func": generate_signals_breakout_vol},
    "V30-PULLBACK-CONT-15M": {"family": "pullback_cont", "timeframe": "15m", "func": generate_signals_pullback_cont},
    "V30-PULLBACK-CONT-30M": {"family": "pullback_cont", "timeframe": "30m", "func": generate_signals_pullback_cont},
    "V30-LIQUIDITY-REVERSAL-15M": {"family": "liquidity_reversal", "timeframe": "15m", "func": generate_signals_liquidity_reversal},
    "V30-LIQUIDITY-REVERSAL-1H": {"family": "liquidity_reversal", "timeframe": "1h", "func": generate_signals_liquidity_reversal},
    "V30-MTF-CONFLUENCE-30M": {"family": "mtf_confluence", "timeframe": "30m", "func": generate_signals_mtf_confluence},
    "V30-MTF-CONFLUENCE-1H": {"family": "mtf_confluence", "timeframe": "1h", "func": generate_signals_mtf_confluence},
    "V30-VOL-ADAPTIVE-1H": {"family": "vol_adaptive", "timeframe": "1h", "func": generate_signals_vol_adaptive},
    "V30-VOL-ADAPTIVE-4H": {"family": "vol_adaptive", "timeframe": "4h", "func": generate_signals_vol_adaptive},
    "V30-HYBRID-REGIME-1H": {"family": "regime_trend", "timeframe": "1h", "func": generate_signals_regime_trend},
    "V30-STRUCTURE-SWEEP-30M": {"family": "liquidity_reversal", "timeframe": "30m", "func": generate_signals_liquidity_reversal},
}
