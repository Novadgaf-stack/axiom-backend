"""
NEXUS-7 — RESEARCH V26 STRATEGY LIBRARY
Independently tested entry/exit logic across liquid pairs and multi-timeframes (15m, 30m, 1h).
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any


SUPPORTED_PAIRS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
    "XRP/USDT", "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT"
]

TIMEFRAMES = ["15m", "30m", "1h"]


class V26StrategyCandidate:
    """Base interface for V26 strategy candidates."""
    def __init__(self, name: str, timeframe: str):
        self.name = name
        self.timeframe = timeframe

    def generate_signals(self, df: pd.DataFrame, htf_df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Returns dataframe with 'signal' column: 1 (BUY), -1 (SELL), 0 (HOLD)."""
        raise NotImplementedError


class MTFTrendPullback(V26StrategyCandidate):
    """
    Candidate 1: Higher Timeframe Trend + Pullback Rejection
    HTF (1h/4h) defines trend bias; LTF (15m/30m) enters on RSI pullback + EMA touch.
    """
    def __init__(self, timeframe: str = "30m", rsi_oversold: float = 42.0, rsi_overbought: float = 58.0):
        super().__init__(name="MTF_Trend_Pullback", timeframe=timeframe)
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def generate_signals(self, df: pd.DataFrame, htf_df: pd.DataFrame | None = None) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 0

        # Calculate indicators if missing
        if "ema_fast" not in df.columns:
            df["ema_fast"] = df["close"].ewm(span=9, adjust=False).mean()
        if "ema_slow" not in df.columns:
            df["ema_slow"] = df["close"].ewm(span=21, adjust=False).mean()
        if "ema_trend" not in df.columns:
            df["ema_trend"] = df["close"].ewm(span=50, adjust=False).mean()
        if "rsi" not in df.columns:
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss.replace(0, 1e-9))
            df["rsi"] = 100 - (100 / (1 + rs))

        # HTF Trend Filter: If htf_df provided, require HTF close > HTF ema_trend
        htf_bullish = True
        htf_bearish = True
        if htf_df is not None and not htf_df.empty:
            htf_last_close = float(htf_df["close"].iloc[-1])
            htf_last_ema = float(htf_df["close"].ewm(span=50, adjust=False).mean().iloc[-1])
            htf_bullish = htf_last_close > htf_last_ema
            htf_bearish = htf_last_close < htf_last_ema

        # BUY: Bullish trend (close > ema_trend) & RSI pulled back < oversold & close touched ema_slow
        buy_cond = (
            (df["close"] > df["ema_trend"]) &
            (df["rsi"] < self.rsi_oversold) &
            (df["low"] <= df["ema_slow"]) &
            htf_bullish
        )

        # SELL: Bearish trend & RSI overbought > overbought & close touched ema_slow
        sell_cond = (
            (df["close"] < df["ema_trend"]) &
            (df["rsi"] > self.rsi_overbought) &
            (df["high"] >= df["ema_slow"]) &
            htf_bearish
        )

        df.loc[buy_cond, "signal"] = 1
        df.loc[sell_cond, "signal"] = -1
        return df


class BreakoutVolumeExpansion(V26StrategyCandidate):
    """
    Candidate 2: Volatility Squeeze Breakout + Volume Expansion
    Enters on Bollinger Band breakout when bandwidth is compressed and volume expands > 1.5x.
    """
    def __init__(self, timeframe: str = "15m", bb_period: int = 20, vol_mult: float = 1.4):
        super().__init__(name="Breakout_Volume_Expansion", timeframe=timeframe)
        self.bb_period = bb_period
        self.vol_mult = vol_mult

    def generate_signals(self, df: pd.DataFrame, htf_df: pd.DataFrame | None = None) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 0

        rolling_mean = df["close"].rolling(window=self.bb_period).mean()
        rolling_std = df["close"].rolling(window=self.bb_period).std()
        df["bb_upper"] = rolling_mean + (rolling_std * 2.0)
        df["bb_lower"] = rolling_mean - (rolling_std * 2.0)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / rolling_mean
        df["vol_sma"] = df["volume"].rolling(window=20).mean()

        # Volatility squeeze: bandwidth in lower 30th percentile of rolling 100 bars
        width_threshold = df["bb_width"].rolling(window=100).quantile(0.35)
        volume_expansion = df["volume"] > (df["vol_sma"] * self.vol_mult)

        buy_cond = (df["close"] > df["bb_upper"]) & (df["bb_width"] <= width_threshold) & volume_expansion
        sell_cond = (df["close"] < df["bb_lower"]) & (df["bb_width"] <= width_threshold) & volume_expansion

        df.loc[buy_cond, "signal"] = 1
        df.loc[sell_cond, "signal"] = -1
        return df


class AdaptiveMeanReversion(V26StrategyCandidate):
    """
    Candidate 3: Adaptive Mean Reversion with Trend Filter
    Counter-trend entries only when ATR volatility is low to moderate.
    """
    def __init__(self, timeframe: str = "30m", rsi_buy: float = 30.0, rsi_sell: float = 70.0):
        super().__init__(name="Adaptive_Mean_Reversion", timeframe=timeframe)
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def generate_signals(self, df: pd.DataFrame, htf_df: pd.DataFrame | None = None) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 0

        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, 1e-9))
        df["rsi"] = 100 - (100 / (1 + rs))

        rolling_mean = df["close"].rolling(window=20).mean()
        rolling_std = df["close"].rolling(window=20).std()
        df["bb_lower"] = rolling_mean - (rolling_std * 2.2)
        df["bb_upper"] = rolling_mean + (rolling_std * 2.2)

        buy_cond = (df["close"] <= df["bb_lower"]) & (df["rsi"] <= self.rsi_buy)
        sell_cond = (df["close"] >= df["bb_upper"]) & (df["rsi"] >= self.rsi_sell)

        df.loc[buy_cond, "signal"] = 1
        df.loc[sell_cond, "signal"] = -1
        return df


class MomentumContinuation(V26StrategyCandidate):
    """
    Candidate 4: Dual Moving Average Cross + MACD Expansion
    Momentum continuation on 15m/30m timeframe.
    """
    def __init__(self, timeframe: str = "15m"):
        super().__init__(name="Momentum_Continuation", timeframe=timeframe)

    def generate_signals(self, df: pd.DataFrame, htf_df: pd.DataFrame | None = None) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 0

        df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
        df["macd_line"] = df["close"].ewm(span=12, adjust=False).mean() - df["close"].ewm(span=26, adjust=False).mean()
        df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd_line"] - df["macd_signal"]

        buy_cond = (
            (df["ema9"] > df["ema21"]) &
            (df["ema9"].shift(1) <= df["ema21"].shift(1)) &
            (df["macd_hist"] > 0)
        )
        sell_cond = (
            (df["ema9"] < df["ema21"]) &
            (df["ema9"].shift(1) >= df["ema21"].shift(1)) &
            (df["macd_hist"] < 0)
        )

        df.loc[buy_cond, "signal"] = 1
        df.loc[sell_cond, "signal"] = -1
        return df


class DynamicRegimeFilter(V26StrategyCandidate):
    """
    Candidate 5: Choppiness Index Filter + Donchian Channel Breakout
    Filters out range-bound markets (CHOP > 50) and trades trending breakouts.
    """
    def __init__(self, timeframe: str = "1h", channel_period: int = 24):
        super().__init__(name="Dynamic_Regime_Filter", timeframe=timeframe)
        self.channel_period = channel_period

    def generate_signals(self, df: pd.DataFrame, htf_df: pd.DataFrame | None = None) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 0

        # Donchian channels
        df["dc_high"] = df["high"].rolling(window=self.channel_period).max().shift(1)
        df["dc_low"] = df["low"].rolling(window=self.channel_period).min().shift(1)

        # Choppiness Index approximation
        tr = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                (df["high"] - df["close"].shift(1)).abs(),
                (df["low"] - df["close"].shift(1)).abs()
            )
        )
        atr_sum = tr.rolling(window=14).sum()
        high_low_range = df["high"].rolling(window=14).max() - df["low"].rolling(window=14).min()
        chop = 100 * np.log10(atr_sum / (high_low_range.replace(0, 1e-9))) / np.log10(14)
        df["chop"] = chop

        # Trending regime: CHOP < 50
        trending = df["chop"] < 50.0

        buy_cond = (df["close"] > df["dc_high"]) & trending
        sell_cond = (df["close"] < df["dc_low"]) & trending

        df.loc[buy_cond, "signal"] = 1
        df.loc[sell_cond, "signal"] = -1
        return df
