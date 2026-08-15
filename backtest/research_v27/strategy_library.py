"""
NEXUS-7 — RESEARCH V27 STRATEGY LIBRARY
Candidate strategy families for Targeted Expectancy Research (0.8 - 1.8 trades/day target).
Evaluates 12 liquid pairs across 15m, 30m, 1h, and 4h timeframes.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

SUPPORTED_PAIRS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
    "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT",
    "NEAR/USDT", "SUI/USDT"
]

TIMEFRAMES = ["15m", "30m", "1h", "4h"]


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates EMAs, RSI, ATR, Bollinger Bands, ADX, MACD, and Volume MAs."""
    df = df.copy()
    if len(df) < 50:
        return df

    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    volume = df["volume"].values

    # EMAs
    df["ema8"] = pd.Series(close).ewm(span=8, adjust=False).mean()
    df["ema20"] = pd.Series(close).ewm(span=20, adjust=False).mean()
    df["ema50"] = pd.Series(close).ewm(span=50, adjust=False).mean()
    df["ema200"] = pd.Series(close).ewm(span=200, adjust=False).mean()

    # RSI
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))

    # ATR
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    df["atr"] = pd.Series(tr).rolling(window=14).mean()

    # Bollinger Bands
    sma20 = pd.Series(close).rolling(window=20).mean()
    std20 = pd.Series(close).rolling(window=20).std()
    df["bb_upper"] = sma20 + (2.0 * std20)
    df["bb_lower"] = sma20 - (2.0 * std20)
    df["bb_middle"] = sma20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / (sma20 + 1e-10)

    # Volume MA
    df["vol_ma20"] = pd.Series(volume).rolling(window=20).mean()

    # ADX (approximate directional index)
    up_move = high - np.roll(high, 1)
    down_move = np.roll(low, 1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_ser = df["atr"].values + 1e-10
    plus_di = 100 * (pd.Series(plus_dm).rolling(14).mean() / atr_ser)
    minus_di = 100 * (pd.Series(minus_dm).rolling(14).mean() / atr_ser)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    df["adx"] = pd.Series(dx).rolling(14).mean()

    # MACD
    ema12 = pd.Series(close).ewm(span=12, adjust=False).mean()
    ema26 = pd.Series(close).ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    return df


class BaseV27Candidate:
    """Base class for V27 research candidates."""

    def __init__(self, candidate_id: str, family: str, timeframe: str, min_confidence: float = 0.80):
        self.candidate_id = candidate_id
        self.family = family
        self.timeframe = timeframe
        self.min_confidence = min_confidence

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError


class TargetedMTFPullback(BaseV27Candidate):
    """
    Family 1: Targeted Multi-Timeframe Trend Pullback.
    Entry: HTF trend UP (EMA20 > EMA50) + LTF pullback to EMA20 with RSI between 40 and 55 + Volume > 1.2x MA20.
    """

    def __init__(self, timeframe: str = "15m", min_confidence: float = 0.82):
        super().__init__(
            candidate_id=f"V27-MTF-PULLBACK-{timeframe.upper()}",
            family="Targeted MTF Pullback",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        df = calculate_indicators(df)
        if len(df) < 50:
            return []

        htf_bullish = True
        if htf_df is not None and len(htf_df) >= 50:
            htf_calc = calculate_indicators(htf_df)
            last_htf = htf_calc.iloc[-1]
            htf_bullish = last_htf["ema20"] > last_htf["ema50"]

        signals = []
        for i in range(40, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            if not htf_bullish:
                continue

            # LTF pullback condition
            ema_trend = row["ema20"] > row["ema50"]
            pullback = (prev["low"] <= prev["ema20"]) and (row["close"] > row["ema20"])
            rsi_ok = 38 <= row["rsi"] <= 56
            vol_ok = row["volume"] >= 1.15 * row["vol_ma20"]

            if ema_trend and pullback and rsi_ok and vol_ok:
                confidence = 0.84 if row["adx"] > 22 else 0.80
                if confidence >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.5 * atr_val),
                        "take_profit": row["close"] + (2.5 * atr_val),
                        "confidence": confidence,
                        "candidate_id": self.candidate_id
                    })

        return signals


class FilteredBreakoutExpansion(BaseV27Candidate):
    """
    Family 2: Volatility Squeeze Breakout + Volume Expansion.
    Entry: BB width < 20th percentile + Close breaks above BB Upper + Volume > 1.4x MA20.
    """

    def __init__(self, timeframe: str = "30m", min_confidence: float = 0.82):
        super().__init__(
            candidate_id=f"V27-BREAKOUT-VOL-{timeframe.upper()}",
            family="Filtered Breakout Expansion",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        df = calculate_indicators(df)
        if len(df) < 60:
            return []

        signals = []
        for i in range(50, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            recent_bb_widths = df["bb_width"].iloc[i - 30:i]
            squeeze_thresh = np.percentile(recent_bb_widths.dropna(), 25)

            bb_squeeze = prev["bb_width"] <= squeeze_thresh
            breakout = (prev["close"] <= prev["bb_upper"]) and (row["close"] > row["bb_upper"])
            vol_expansion = row["volume"] >= 1.35 * row["vol_ma20"]
            adx_ok = row["adx"] >= 18

            if bb_squeeze and breakout and vol_expansion and adx_ok:
                confidence = 0.85 if row["macd_hist"] > 0 else 0.81
                if confidence >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.6 * atr_val),
                        "take_profit": row["close"] + (2.4 * atr_val),
                        "confidence": confidence,
                        "candidate_id": self.candidate_id
                    })

        return signals


class AdaptiveMeanReversion(BaseV27Candidate):
    """
    Family 3: Regime-Constrained Adaptive Mean Reversion.
    Entry: Low ADX (< 20 ranging market) + RSI < 32 oversold + price < BB Lower - 0.5 * ATR.
    """

    def __init__(self, timeframe: str = "15m", min_confidence: float = 0.80):
        super().__init__(
            candidate_id=f"V27-MEAN-REV-{timeframe.upper()}",
            family="Adaptive Mean Reversion",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        df = calculate_indicators(df)
        if len(df) < 50:
            return []

        signals = []
        for i in range(40, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            low_adx = row["adx"] < 21
            oversold_rsi = row["rsi"] < 33
            bb_overshoot = row["close"] < (row["bb_lower"] - 0.2 * row["atr"])

            if low_adx and oversold_rsi and bb_overshoot:
                confidence = 0.83 if row["rsi"] < 28 else 0.80
                if confidence >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.4 * atr_val),
                        "take_profit": row["bb_middle"],  # Mean reversion to BB middle
                        "confidence": confidence,
                        "candidate_id": self.candidate_id
                    })

        return signals


class MomentumContinuation(BaseV27Candidate):
    """
    Family 4: Multi-Factor Momentum Continuation.
    Entry: ADX > 25 (strong trend) + MACD Hist expansion + EMA8 > EMA21 > EMA50.
    """

    def __init__(self, timeframe: str = "1h", min_confidence: float = 0.82):
        super().__init__(
            candidate_id=f"V27-MOM-CONT-{timeframe.upper()}",
            family="Momentum Continuation",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        df = calculate_indicators(df)
        if len(df) < 50:
            return []

        signals = []
        for i in range(40, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            strong_trend = row["adx"] > 24
            ema_aligned = row["ema8"] > row["ema20"] > row["ema50"]
            macd_expanding = (row["macd_hist"] > prev["macd_hist"]) and (row["macd_hist"] > 0)
            rsi_valid = 50 <= row["rsi"] <= 68

            if strong_trend and ema_aligned and macd_expanding and rsi_valid:
                confidence = 0.86 if row["adx"] > 30 else 0.82
                if confidence >= self.min_confidence:
                    atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                    signals.append({
                        "timestamp": row["timestamp"],
                        "index": i,
                        "side": "BUY",
                        "price": row["close"],
                        "stop_loss": row["close"] - (1.5 * atr_val),
                        "take_profit": row["close"] + (2.5 * atr_val),
                        "confidence": confidence,
                        "candidate_id": self.candidate_id
                    })

        return signals


class DynamicConfluenceFilter(BaseV27Candidate):
    """
    Family 5: Dynamic Multi-Timeframe Confluence.
    Targeted specifically to generate ~1 to 1.5 high-conviction trades/day portfolio-wide.
    Combines multi-indicator composite score >= 82%.
    """

    def __init__(self, timeframe: str = "30m", min_confidence: float = 0.83):
        super().__init__(
            candidate_id=f"V27-CONFLUENCE-{timeframe.upper()}",
            family="Dynamic Multi-Timeframe Confluence",
            timeframe=timeframe,
            min_confidence=min_confidence
        )

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        df = calculate_indicators(df)
        if len(df) < 50:
            return []

        signals = []
        for i in range(40, len(df)):
            row = df.iloc[i]

            score = 0.0

            # Trend score (30%)
            if row["ema20"] > row["ema50"]:
                score += 0.30

            # RSI momentum score (20%)
            if 48 <= row["rsi"] <= 64:
                score += 0.20

            # ADX trend strength score (20%)
            if row["adx"] >= 22:
                score += 0.20

            # Volume confirmation score (15%)
            if row["volume"] >= 1.2 * row["vol_ma20"]:
                score += 0.15

            # MACD bullish score (15%)
            if row["macd_hist"] > 0:
                score += 0.15

            if score >= self.min_confidence:
                atr_val = row["atr"] if not np.isnan(row["atr"]) and row["atr"] > 0 else row["close"] * 0.015
                signals.append({
                    "timestamp": row["timestamp"],
                    "index": i,
                    "side": "BUY",
                    "price": row["close"],
                    "stop_loss": row["close"] - (1.5 * atr_val),
                    "take_profit": row["close"] + (2.6 * atr_val),
                    "confidence": score,
                    "candidate_id": self.candidate_id
                })

        return signals
