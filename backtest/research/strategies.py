"""
Independent Strategy Families (EXP-001 through EXP-006) for NEXUS-7 Research Reset.
Implements economically distinct trading hypotheses without parameter optimization.
"""
import dataclasses
import math
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from app.indicators import _adx, _atr, _ema


class StrategyFamilyBase:
    """Base class for research strategy families."""
    def __init__(self, family_id: str, name: str, hypothesis: str):
        self.family_id = family_id
        self.name = name
        self.hypothesis = hypothesis

    def generate_signals(self, df_1h: pd.DataFrame) -> pd.Series:
        """
        Returns Series of signals: +1 (BUY), -1 (SELL), 0 (HOLD).
        """
        raise NotImplementedError


class StrategyATrendFollowing(StrategyFamilyBase):
    """
    EXP-001: Multi-Timeframe Trend Following & Volatility-Adjusted Trailing Exits.
    Hypothesis: Large directional crypto moves exhibit persistence over long horizons.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-001",
            name="Strategy A — Multi-Timeframe Trend Following",
            hypothesis="Directional crypto momentum exhibits persistence across multi-timeframe trend alignment.",
        )

    def generate_signals(self, df_1h: pd.DataFrame) -> pd.Series:
        df = df_1h.copy()
        ema_50 = _ema(df["close"], 50)
        ema_200 = _ema(df["close"], 200)
        adx_1h = _adx(df, 14)
        donchian_high = df["high"].rolling(20).max().shift(1)

        # Trend alignment + Donchian breakout
        bullish_trend = (df["close"] > ema_50) & (ema_50 > ema_200) & (adx_1h >= 20.0)
        breakout = df["close"] > donchian_high

        signals = pd.Series(0, index=df.index)
        signals[bullish_trend & breakout] = 1
        return signals


class StrategyBVolatilityBreakout(StrategyFamilyBase):
    """
    EXP-002: Volatility Compression to Range Expansion Breakout.
    Hypothesis: Transition from compressed volatility into expansion produces directional continuation.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-002",
            name="Strategy B — Volatility Breakout",
            hypothesis="Volatility compression (low ATR ratio) followed by range expansion signals explosive directional trend.",
        )

    def generate_signals(self, df_1h: pd.DataFrame) -> pd.Series:
        df = df_1h.copy()
        atr_14 = _atr(df, 14)
        atr_50_avg = atr_14.rolling(50).mean().replace(0, 1e-9)
        vol_compression = (atr_14 / atr_50_avg) < 0.85  # Squeeze condition

        ema_20 = _ema(df["close"], 20)
        keltner_upper = ema_20 + (1.5 * atr_14)
        breakout = df["close"] > keltner_upper.shift(1)

        signals = pd.Series(0, index=df.index)
        # Squeeze in recent 5 bars + Keltner upper breakout
        squeeze_recent = vol_compression.rolling(5).max() > 0
        signals[squeeze_recent & breakout] = 1
        return signals


class StrategyCMeanReversion(StrategyFamilyBase):
    """
    EXP-003: Standardized Price Z-Score Mean Reversion.
    Hypothesis: Short-term price dislocations revert toward rolling equilibrium in non-trending regimes.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-003",
            name="Strategy C — Standardized Z-Score Mean Reversion",
            hypothesis="Price dislocations > 2.0 std deviations from mean revert to equilibrium in ranging markets.",
        )

    def generate_signals(self, df_1h: pd.DataFrame) -> pd.Series:
        df = df_1h.copy()
        adx_1h = _adx(df, 14)
        ranging_regime = adx_1h < 20.0

        ema_20 = _ema(df["close"], 20)
        std_20 = df["close"].rolling(20).std().replace(0, 1e-9)
        z_score = (df["close"] - ema_20) / std_20

        signals = pd.Series(0, index=df.index)
        signals[ranging_regime & (z_score < -2.0)] = 1  # Oversold mean reversion
        return signals


class StrategyDRelativeStrength(StrategyFamilyBase):
    """
    EXP-004: Cross-Sectional Multi-Asset Relative Strength.
    Hypothesis: Top relative strength assets outperform weaker assets over rolling horizons.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-004",
            name="Strategy D — Cross-Sectional Relative Strength",
            hypothesis="Cross-sectional momentum ranking identifies persistent outperforming crypto assets.",
        )

    def generate_signals(self, df_1h: pd.DataFrame) -> pd.Series:
        df = df_1h.copy()
        ret_30d = df["close"].pct_change(120)  # 5-day / 120-hour return
        vol_30d = df["close"].pct_change().rolling(120).std().replace(0, 1e-9)
        sharpe_score = ret_30d / vol_30d

        ema_50 = _ema(df["close"], 50)
        uptrend = df["close"] > ema_50

        signals = pd.Series(0, index=df.index)
        # Signal top 25% momentum percentile
        mom_percentile = sharpe_score.rolling(240).rank(pct=True)
        signals[uptrend & (mom_percentile > 0.75)] = 1
        return signals


class StrategyERegimeAllocation(StrategyFamilyBase):
    """
    EXP-005: Market Regime Allocation Engine.
    Hypothesis: Allocating between Trend-Following and Mean-Reversion based on pre-classified ADX regime improves expectancy.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-005",
            name="Strategy E — Market Regime Allocation Engine",
            hypothesis="Switching strategy rules based on macro ADX regime eliminates counter-regime drag.",
        )

    def generate_signals(self, df_1h: pd.DataFrame) -> pd.Series:
        df = df_1h.copy()
        adx_1h = _adx(df, 14)

        sig_trend = StrategyATrendFollowing().generate_signals(df)
        sig_reversion = StrategyCMeanReversion().generate_signals(df)

        signals = pd.Series(0, index=df.index)
        # Allocate Strategy A in Trend (ADX >= 25), Strategy C in Range (ADX < 20)
        signals[adx_1h >= 25.0] = sig_trend[adx_1h >= 25.0]
        signals[adx_1h < 20.0] = sig_reversion[adx_1h < 20.0]
        return signals


class StrategyFCostAwareForecasting(StrategyFamilyBase):
    """
    EXP-006: Cost-Aware Expected Return Forecasting.
    Hypothesis: Trade only when Expected Gross Edge E[R | X] > C_total + Minimum Economic Margin (M).
    """
    def __init__(self, min_economic_margin: float = 0.003):  # 0.30% minimum margin over costs
        super().__init__(
            family_id="EXP-006",
            name="Strategy F — Cost-Aware Expected Return Gate",
            hypothesis="Trade placement conditioned on E[R | X] > C_total + M suppresses negative-expectancy trades.",
        )
        self.min_economic_margin = min_economic_margin

    def generate_signals(self, df_1h: pd.DataFrame) -> pd.Series:
        df = df_1h.copy()
        atr_14 = _atr(df, 14)
        adx_14 = _adx(df, 14)
        ema_21 = _ema(df["close"], 21)
        ema_50 = _ema(df["close"], 50)

        # Estimate expected return E[R | X] from trend velocity & volume
        trend_score = (df["close"] - ema_50) / ema_50
        vol_score = (atr_14 / df["close"])

        # Expected 24h gross return estimate
        expected_gross_return = np.abs(trend_score) * (adx_14 / 100.0) + (vol_score * 0.5)

        # Total Roundtrip Cost C_total (Normal Maker = 0.04% fee * 2 + 0.01% slip * 2 = 0.10%)
        c_total = 0.0010 + self.min_economic_margin  # 0.10% cost + 0.30% margin = 0.40% required edge

        pullback_setup = (df["close"] > ema_50) & (df["close"] <= ema_21 * 1.005)

        signals = pd.Series(0, index=df.index)
        # Execute ONLY if expected gross edge exceeds total cost + margin threshold
        signals[pullback_setup & (expected_gross_return > c_total)] = 1
        return signals


def get_all_research_strategies() -> List[StrategyFamilyBase]:
    """Returns instance list of all 6 strategy families."""
    return [
        StrategyATrendFollowing(),
        StrategyBVolatilityBreakout(),
        StrategyCMeanReversion(),
        StrategyDRelativeStrength(),
        StrategyERegimeAllocation(),
        StrategyFCostAwareForecasting(),
    ]
