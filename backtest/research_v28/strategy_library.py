"""
NEXUS-7 — RESEARCH V28 STRATEGY LIBRARY
Implements 5 candidate strategy families targeting ~0.8 to 1.5 genuine trades/day.
Evaluates 12 liquid pairs across 15m, 30m, 1h, and 4h timeframes.
Includes parameter sensitivity hooks for robustness testing (±10% threshold variation).
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional


def calculate_indicators(df: pd.DataFrame, param_mult: float = 1.0) -> pd.DataFrame:
    """Calculates EMAs, RSI, ATR, Bollinger Bands, ADX, MACD, and Volume MAs with optional parameter scaling."""
    df = df.copy()
    if len(df) < 50:
        return df

    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    volume = df["volume"].values

    # Scaled indicator windows
    ema_fast = max(5, int(20 * param_mult))
    ema_slow = max(15, int(50 * param_mult))
    rsi_len = max(5, int(14 * param_mult))
    atr_len = max(5, int(14 * param_mult))
    vol_len = max(5, int(20 * param_mult))

    # EMAs
    df["ema20"] = pd.Series(close).ewm(span=ema_fast, adjust=False).mean()
    df["ema50"] = pd.Series(close).ewm(span=ema_slow, adjust=False).mean()
    df["ema200"] = pd.Series(close).ewm(span=200, adjust=False).mean()

    # RSI
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_len).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_len).mean()
    rs = gain / (loss + 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))

    # ATR
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    df["atr"] = pd.Series(tr).rolling(window=atr_len).mean()

    # Bollinger Bands
    sma20 = pd.Series(close).rolling(window=vol_len).mean()
    std20 = pd.Series(close).rolling(window=vol_len).std()
    df["bb_upper"] = sma20 + (2.0 * std20)
    df["bb_lower"] = sma20 - (2.0 * std20)
    df["bb_middle"] = sma20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / (sma20 + 1e-10)

    # Volume MA
    df["vol_ma20"] = pd.Series(volume).rolling(window=vol_len).mean()

    # ADX
    up_move = high - np.roll(high, 1)
    down_move = np.roll(low, 1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_ser = df["atr"].values + 1e-10
    plus_di = 100 * (pd.Series(plus_dm).rolling(rsi_len).mean() / atr_ser)
    minus_di = 100 * (pd.Series(minus_dm).rolling(rsi_len).mean() / atr_ser)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    df["adx"] = pd.Series(dx).rolling(rsi_len).mean()

    # MACD
    ema12 = pd.Series(close).ewm(span=12, adjust=False).mean()
    ema26 = pd.Series(close).ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    return df


class BaseV28Candidate:
    """Base class for V28 research candidates."""

    def __init__(self, candidate_id: str, family: str, timeframe: str, min_confidence: float = 0.80):
        self.candidate_id = candidate_id
        self.family = family
        self.timeframe = timeframe
        self.min_confidence = min_confidence

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None, param_mult: float = 1.0) -> List[Dict[str, Any]]:
        raise NotImplementedError


class VolatilityBreakoutTrend(BaseV28Candidate):
    """
    Family 1: Volatility Expansion Breakout + Trend Confirmation.
    Entry: Close > BB Upper + Volume > 1.3x Vol MA + EMA20 > EMA50 + ADX > 20.
    Target: ~1 trade/day on 30m/1h.
    """

    def __init__(self, timeframe: str = "30m", min_confidence: float = 0.80):
        super().__init__(
            candidate_id=f"V28-BREAKOUT-TREND-{timeframe.upper()}",
            family="Volatility Breakout Trend",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None, param_mult: float = 1.0) -> List[Dict[str, Any]]:
        df = calculate_indicators(df, param_mult=param_mult)
        if len(df) < 60:
            return []

        signals = []
        vol_mult = 1.30 * param_mult
        adx_thresh = 20 * param_mult

        for i in range(50, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            bb_break = (prev["close"] <= prev["bb_upper"]) and (row["close"] > row["bb_upper"])
            trend_ok = row["ema20"] > row["ema50"]
            vol_ok = row["volume"] >= vol_mult * row["vol_ma20"]
            adx_ok = row["adx"] >= adx_thresh

            if bb_break and trend_ok and vol_ok and adx_ok:
                conf = 0.85 if row["macd_hist"] > 0 else 0.80
                if conf >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.5 * atr_val),
                        "take_profit": row["close"] + (2.5 * atr_val),
                        "confidence": conf,
                        "candidate_id": self.candidate_id
                    })

        return signals


class MultiTimeframeStructurePullback(BaseV28Candidate):
    """
    Family 2: Multi-Timeframe Trend Structure Pullback.
    Entry: HTF EMA20 > EMA50 + LTF pullback to EMA20 + RSI between 42 and 54 + Volume > 1.2x Vol MA.
    Target: ~1-1.5 trades/day on 15m/30m.
    """

    def __init__(self, timeframe: str = "30m", min_confidence: float = 0.80):
        super().__init__(
            candidate_id=f"V28-MTF-STRUCTURE-{timeframe.upper()}",
            family="MTF Structure Pullback",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None, param_mult: float = 1.0) -> List[Dict[str, Any]]:
        df = calculate_indicators(df, param_mult=param_mult)
        if len(df) < 50:
            return []

        htf_bullish = True
        if htf_df is not None and len(htf_df) >= 50:
            htf_calc = calculate_indicators(htf_df, param_mult=param_mult)
            last_htf = htf_calc.iloc[-1]
            htf_bullish = last_htf["ema20"] > last_htf["ema50"]

        signals = []
        rsi_low = 42 * param_mult
        rsi_high = 54 * param_mult

        for i in range(40, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            if not htf_bullish:
                continue

            ema_trend = row["ema20"] > row["ema50"]
            pullback = (prev["low"] <= prev["ema20"]) and (row["close"] > row["ema20"])
            rsi_ok = rsi_low <= row["rsi"] <= rsi_high
            vol_ok = row["volume"] >= 1.20 * row["vol_ma20"]

            if ema_trend and pullback and rsi_ok and vol_ok:
                conf = 0.84 if row["adx"] > 22 else 0.80
                if conf >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.6 * atr_val),
                        "take_profit": row["close"] + (2.4 * atr_val),
                        "confidence": conf,
                        "candidate_id": self.candidate_id
                    })

        return signals


class RegimeAdaptiveMeanReversion(BaseV28Candidate):
    """
    Family 3: Regime-Adaptive Mean Reversion.
    Entry: Low ADX (< 20 ranging market) + RSI < 30 oversold + Price < BB Lower - 0.3 * ATR.
    Target: ~0.8-1.2 trades/day on 15m/30m.
    """

    def __init__(self, timeframe: str = "30m", min_confidence: float = 0.80):
        super().__init__(
            candidate_id=f"V28-REGIME-MEANREV-{timeframe.upper()}",
            family="Regime Adaptive Mean Reversion",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None, param_mult: float = 1.0) -> List[Dict[str, Any]]:
        df = calculate_indicators(df, param_mult=param_mult)
        if len(df) < 50:
            return []

        signals = []
        adx_limit = 20 * param_mult
        rsi_limit = 30 * param_mult

        for i in range(40, len(df)):
            row = df.iloc[i]

            low_adx = row["adx"] < adx_limit
            oversold = row["rsi"] < rsi_limit
            bb_overshoot = row["close"] < (row["bb_lower"] - 0.3 * row["atr"])

            if low_adx and oversold and bb_overshoot:
                conf = 0.83 if row["rsi"] < 25 else 0.80
                if conf >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.4 * atr_val),
                        "take_profit": row["bb_middle"],
                        "confidence": conf,
                        "candidate_id": self.candidate_id
                    })

        return signals


class MomentumSqueezeContinuation(BaseV28Candidate):
    """
    Family 4: Momentum Squeeze Continuation.
    Entry: BB width < 25th percentile + MACD histogram expansion + Volume > 1.25x Vol MA.
    Target: ~1 trade/day on 30m/1h.
    """

    def __init__(self, timeframe: str = "30m", min_confidence: float = 0.80):
        super().__init__(
            candidate_id=f"V28-MOM-SQUEEZE-{timeframe.upper()}",
            family="Momentum Squeeze Continuation",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None, param_mult: float = 1.0) -> List[Dict[str, Any]]:
        df = calculate_indicators(df, param_mult=param_mult)
        if len(df) < 60:
            return []

        signals = []
        vol_thresh = 1.25 * param_mult

        for i in range(50, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            recent_widths = df["bb_width"].iloc[i - 30:i]
            squeeze = prev["bb_width"] <= np.percentile(recent_widths.dropna(), 25)
            macd_expansion = (row["macd_hist"] > prev["macd_hist"]) and (row["macd_hist"] > 0)
            vol_ok = row["volume"] >= vol_thresh * row["vol_ma20"]

            if squeeze and macd_expansion and vol_ok:
                conf = 0.84 if row["adx"] > 20 else 0.80
                if conf >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.5 * atr_val),
                        "take_profit": row["close"] + (2.5 * atr_val),
                        "confidence": conf,
                        "candidate_id": self.candidate_id
                    })

        return signals


class DynamicVolatilityConfluenceFilter(BaseV28Candidate):
    """
    Family 5: Dynamic Volatility Confluence Filter.
    Entry: EMA20 > EMA50 + ADX > 25 + RSI between 45 and 60 + Volume > 1.35x Vol MA.
    Target: ~0.8-1.2 trades/day on 1h/4h.
    """

    def __init__(self, timeframe: str = "1h", min_confidence: float = 0.80):
        super().__init__(
            candidate_id=f"V28-CONFLUENCE-FILTER-{timeframe.upper()}",
            family="Dynamic Volatility Confluence Filter",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None, param_mult: float = 1.0) -> List[Dict[str, Any]]:
        df = calculate_indicators(df, param_mult=param_mult)
        if len(df) < 50:
            return []

        signals = []
        adx_thresh = 25 * param_mult
        vol_thresh = 1.35 * param_mult

        for i in range(40, len(df)):
            row = df.iloc[i]

            trend_ok = row["ema20"] > row["ema50"]
            adx_ok = row["adx"] >= adx_thresh
            rsi_ok = 45 <= row["rsi"] <= 60
            vol_ok = row["volume"] >= vol_thresh * row["vol_ma20"]

            if trend_ok and adx_ok and rsi_ok and vol_ok:
                conf = 0.85 if row["macd_hist"] > 0 else 0.80
                if conf >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.6 * atr_val),
                        "take_profit": row["close"] + (2.4 * atr_val),
                        "confidence": conf,
                        "candidate_id": self.candidate_id
                    })

        return signals


def get_v28_candidate_pool() -> List[BaseV28Candidate]:
    """Returns candidate pool across the 5 strategy families."""
    return [
        VolatilityBreakoutTrend(timeframe="30m"),
        VolatilityBreakoutTrend(timeframe="1h"),
        MultiTimeframeStructurePullback(timeframe="15m"),
        MultiTimeframeStructurePullback(timeframe="30m"),
        RegimeAdaptiveMeanReversion(timeframe="15m"),
        RegimeAdaptiveMeanReversion(timeframe="30m"),
        MomentumSqueezeContinuation(timeframe="30m"),
        MomentumSqueezeContinuation(timeframe="1h"),
        DynamicVolatilityConfluenceFilter(timeframe="1h"),
        DynamicVolatilityConfluenceFilter(timeframe="4h"),
    ]
