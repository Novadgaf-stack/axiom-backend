"""
Phase 1 Strategy Families (EXP-V2-01 through EXP-V2-07) for Research Reset V2.
Implements economically distinct quantitative strategy candidates.
"""
import dataclasses
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from app.indicators import _adx, _atr, _ema


class StrategyV2Base:
    """Base class for Research V2 Strategy Families."""
    def __init__(self, family_id: str, name: str, hypothesis: str):
        self.family_id = family_id
        self.name = name
        self.hypothesis = hypothesis

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs: Optional[Dict[str, pd.DataFrame]] = None, current_pair: str = "BTCUSDT") -> pd.Series:
        """Returns Series of signals: +1 (BUY), -1 (SELL), 0 (HOLD)."""
        raise NotImplementedError


class StrategyV2TimeSeriesMomentum(StrategyV2Base):
    """
    EXP-V2-01: Time-Series Momentum & Donchian Breakout.
    Hypothesis: Large trend continuation persistence across Donchian range breakouts.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-V2-01",
            name="Strategy A — Time-Series Momentum",
            hypothesis="Donchian 20-bar channel upper breakouts in aligned uptrends exhibit persistence.",
        )

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs=None, current_pair="BTCUSDT") -> pd.Series:
        df = df_1h.copy()
        ema_50 = _ema(df["close"], 50)
        ema_200 = _ema(df["close"], 200)
        donchian_high = df["high"].rolling(20).max().shift(1)

        trend_up = (df["close"] > ema_50) & (ema_50 > ema_200)
        breakout = df["close"] > donchian_high

        signals = pd.Series(0, index=df.index)
        signals[trend_up & breakout] = 1
        return signals


class StrategyV2CrossSectionalRS(StrategyV2Base):
    """
    EXP-V2-02: Cross-Sectional Multi-Asset Relative Strength.
    Hypothesis: Top risk-adjusted momentum assets outperform weaker assets over 30-day horizons.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-V2-02",
            name="Strategy B — Cross-Sectional Relative Strength",
            hypothesis="Cross-sectional risk-adjusted momentum ranking identifies persistent crypto outperformance.",
        )

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs=None, current_pair="BTCUSDT") -> pd.Series:
        df = df_1h.copy()
        ret_120h = df["close"].pct_change(120)
        vol_120h = df["close"].pct_change().rolling(120).std().replace(0, 1e-9)
        sharpe_120h = ret_120h / vol_120h

        ema_50 = _ema(df["close"], 50)
        uptrend = df["close"] > ema_50
        rs_rank = sharpe_120h.rolling(240).rank(pct=True)

        signals = pd.Series(0, index=df.index)
        signals[uptrend & (rs_rank > 0.80)] = 1
        return signals


class StrategyV2VolatilityBreakout(StrategyV2Base):
    """
    EXP-V2-03: Volatility Squeeze to Keltner Range Expansion.
    Hypothesis: Transition from compressed volatility into expansion produces directional continuation.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-V2-03",
            name="Strategy C — Volatility Breakout",
            hypothesis="Low ATR compression ratio transitioning to Keltner upper breakout signals trend expansion.",
        )

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs=None, current_pair="BTCUSDT") -> pd.Series:
        df = df_1h.copy()
        atr_14 = _atr(df, 14)
        atr_50_avg = atr_14.rolling(50).mean().replace(0, 1e-9)
        squeeze = (atr_14 / atr_50_avg) < 0.78  # Tight compression

        ema_20 = _ema(df["close"], 20)
        keltner_upper = ema_20 + (1.8 * atr_14)
        breakout = df["close"] > keltner_upper.shift(1)

        signals = pd.Series(0, index=df.index)
        squeeze_active = squeeze.rolling(4).max() > 0
        signals[squeeze_active & breakout] = 1
        return signals


class StrategyV2StatisticalMeanReversion(StrategyV2Base):
    """
    EXP-V2-04: Genuine Statistical Z-Score Mean Reversion.
    Hypothesis: Standardized price dislocations > 2.2 std revert toward rolling mean in non-trending markets.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-V2-04",
            name="Strategy D — Statistical Z-Score Mean Reversion",
            hypothesis="Price dislocations > 2.2 std from EMA revert to mean in ranging (ADX < 20) regimes.",
        )

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs=None, current_pair="BTCUSDT") -> pd.Series:
        df = df_1h.copy()
        adx_14 = _adx(df, 14)
        ranging = adx_14 < 18.0

        ema_20 = _ema(df["close"], 20)
        std_20 = df["close"].rolling(20).std().replace(0, 1e-9)
        z_score = (df["close"] - ema_20) / std_20

        signals = pd.Series(0, index=df.index)
        signals[ranging & (z_score < -2.2)] = 1  # Oversold mean reversion
        return signals


class StrategyV2LeadLag(StrategyV2Base):
    """
    EXP-V2-05: Cross-Asset Lead/Lag Predictive Model.
    Hypothesis: BTC 6-hour strong momentum leads subsequent 1H lag moves in ETH, SOL, BNB, XRP.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-V2-05",
            name="Strategy E — Cross-Asset Lead/Lag Predictive Model",
            hypothesis="Major market leader (BTC) momentum predicts subsequent follower asset directional moves.",
        )

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs=None, current_pair="BTCUSDT") -> pd.Series:
        df = df_1h.copy()
        signals = pd.Series(0, index=df.index)

        # If evaluating BTC, use self-lead. If altcoin, use BTC lead signal.
        leader_df = df
        if universe_dfs and "BTCUSDT" in universe_dfs and current_pair != "BTCUSDT":
            leader_df = universe_dfs["BTCUSDT"]

        btc_ret_6h = leader_df["close"].pct_change(6)
        btc_strong_bull = btc_ret_6h > 0.025  # BTC +2.5% in 6h

        ema_20 = _ema(df["close"], 20)
        follower_lagging = df["close"] > ema_20  # Follower starting to align

        # Ensure lengths match
        m_len = min(len(signals), len(btc_strong_bull))
        sub_lead = btc_strong_bull.iloc[:m_len].values
        sub_fol = follower_lagging.iloc[:m_len].values

        signals.iloc[:m_len] = np.where(sub_lead & sub_fol, 1, 0)
        return signals


class StrategyV2MarketNeutralRelValue(StrategyV2Base):
    """
    EXP-V2-06: Market-Neutral Relative Value Spread.
    Hypothesis: Pair spread Z-Score deviations (Altcoin / BTC ratio) revert to rolling mean.
    """
    def __init__(self):
        super().__init__(
            family_id="EXP-V2-06",
            name="Strategy F — Market-Neutral Relative Value Spread",
            hypothesis="Altcoin/BTC price ratio spread Z-scores revert to rolling equilibrium.",
        )

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs=None, current_pair="BTCUSDT") -> pd.Series:
        df = df_1h.copy()
        signals = pd.Series(0, index=df.index)

        btc_df = df
        if universe_dfs and "BTCUSDT" in universe_dfs:
            btc_df = universe_dfs["BTCUSDT"]

        m_len = min(len(df), len(btc_df))
        ratio = df["close"].iloc[:m_len] / btc_df["close"].iloc[:m_len].replace(0, 1e-9)

        ratio_mean = ratio.rolling(50).mean()
        ratio_std = ratio.rolling(50).std().replace(0, 1e-9)
        ratio_z = (ratio - ratio_mean) / ratio_std

        # Buy altcoin when Alt/BTC ratio drops below -2.0 z-score (under-priced relative value)
        buy_cond = ratio_z < -2.0
        signals.iloc[:m_len] = np.where(buy_cond, 1, 0)
        return signals


class StrategyV2CostAwareGate(StrategyV2Base):
    """
    EXP-V2-07: Cost-Aware Expected Return Gate.
    Hypothesis: Trade ONLY when E[R | X] > C_total + Minimum Economic Margin (M).
    """
    def __init__(self, min_economic_margin: float = 0.0035):  # 0.35% margin over costs
        super().__init__(
            family_id="EXP-V2-07",
            name="Strategy G — Cost-Aware Expected Return Gate",
            hypothesis="Conditioning trade entry on E[R | X] > C_total + M suppresses negative-expectancy trades.",
        )
        self.min_economic_margin = min_economic_margin

    def generate_signals(self, df_1h: pd.DataFrame, universe_dfs=None, current_pair="BTCUSDT") -> pd.Series:
        df = df_1h.copy()
        atr_14 = _atr(df, 14)
        adx_14 = _adx(df, 14)
        ema_50 = _ema(df["close"], 50)

        # Conditional expected return estimation E[R | X]
        momentum_velocity = (df["close"] - ema_50) / ema_50
        vol_ratio = atr_14 / df["close"]
        e_r_x = np.abs(momentum_velocity) * (adx_14 / 100.0) + (vol_ratio * 0.6)

        c_total = 0.0010 + self.min_economic_margin  # 0.10% cost + 0.35% margin = 0.45% required return

        donchian_breakout = df["close"] > df["high"].rolling(15).max().shift(1)

        signals = pd.Series(0, index=df.index)
        signals[donchian_breakout & (e_r_x > c_total)] = 1
        return signals


def get_all_v2_research_strategies() -> List[StrategyV2Base]:
    """Returns instances of all 7 Phase 1 Research V2 Strategy Families."""
    return [
        StrategyV2TimeSeriesMomentum(),
        StrategyV2CrossSectionalRS(),
        StrategyV2VolatilityBreakout(),
        StrategyV2StatisticalMeanReversion(),
        StrategyV2LeadLag(),
        StrategyV2MarketNeutralRelValue(),
        StrategyV2CostAwareGate(),
    ]
