"""
NEXUS-7 — RESEARCH V3 INDEPENDENT STRATEGY FAMILIES (EXP-V3-01 to EXP-V3-07)
Includes strict data requirements: if funding/OI data is unavailable in OHLCV datasets,
strategies report STATUS = DATA REQUIRED and emit 0 signals cleanly.
"""
import pandas as pd
import numpy as np


class StrategyV3_01_VolCompressionBreakout:
    """EXP-V3-01: Volatility Compression -> Breakout"""
    def __init__(self):
        self.exp_id = "EXP-V3-01"
        self.name = "Strategy A — Volatility Compression -> Breakout"
        self.hypothesis = "Periods of unusually compressed realized volatility precede directional price expansion."

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        if len(df) < 100:
            return pd.Series(0, index=df.index)
            
        close = df["close"]
        high = df["high"]
        low = df["low"]
        
        # ATR 14
        tr = np.maximum(high - low, np.maximum(np.abs(high - close.shift(1)), np.abs(low - close.shift(1))))
        atr = tr.rolling(14).mean()
        
        # ATR Percentile over 100 bars
        atr_pct = atr.rolling(100).apply(lambda s: (s.iloc[-1] - s.min()) / (s.max() - s.min() + 1e-8), raw=False)
        
        # Donchian Upper (20)
        donchian_hi = high.rolling(20).max().shift(1)
        
        # Vol compression (< 0.25 percentile) and close > donchian upper
        sig = ((atr_pct <= 0.25) & (close > donchian_hi)).astype(int)
        return sig


class StrategyV3_02_FundingBasisRegime:
    """EXP-V3-02: Funding / Basis Regime (DATA REQUIRED)"""
    def __init__(self):
        self.exp_id = "EXP-V3-02"
        self.name = "Strategy B — Funding / Basis Regime"
        self.hypothesis = "Extreme futures positioning creates predictable spot/futures price pressure."
        self.requires_external_data = True
        self.data_status = "DATA REQUIRED"

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        # Check if funding_rate or basis is present in DataFrame
        if "funding_rate" in df.columns or "basis" in df.columns:
            # If present, evaluate extreme funding percentile
            funding = df["funding_rate"] if "funding_rate" in df.columns else df["basis"]
            funding_pct = funding.rolling(100).apply(lambda s: (s.iloc[-1] - s.min()) / (s.max() - s.min() + 1e-8), raw=False)
            sig = (funding_pct <= 0.10).astype(int)  # Extreme negative funding (short squeeze opportunity)
            return sig
        # If unavailable, return all 0 signals cleanly
        return pd.Series(0, index=df.index)


class StrategyV3_03_OpenInterestPriceDivergence:
    """EXP-V3-03: Open Interest + Price Divergence (DATA REQUIRED)"""
    def __init__(self):
        self.exp_id = "EXP-V3-03"
        self.name = "Strategy C — Open Interest + Price Divergence"
        self.hypothesis = "Price movement accompanied by unusual changes in Open Interest reveals positioning dynamics."
        self.requires_external_data = True
        self.data_status = "DATA REQUIRED"

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        if "open_interest" in df.columns:
            oi = df["open_interest"]
            close = df["close"]
            oi_change = oi.pct_change(5)
            price_change = close.pct_change(5)
            # Price UP + OI UP (Strong Institutional Accumulation)
            sig = ((price_change > 0.02) & (oi_change > 0.05)).astype(int)
            return sig
        return pd.Series(0, index=df.index)


class StrategyV3_04_VolumePriceImbalance:
    """EXP-V3-04: Volume / Price Imbalance"""
    def __init__(self):
        self.exp_id = "EXP-V3-04"
        self.name = "Strategy D — Volume / Price Imbalance"
        self.hypothesis = "Abnormal volume combined with directional price move predicts continuation."

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        if len(df) < 30:
            return pd.Series(0, index=df.index)
            
        close = df["close"]
        open_p = df["open"]
        vol = df["volume"]
        
        vol_sma = vol.rolling(20).mean()
        vol_ratio = vol / (vol_sma + 1e-8)
        price_ret = (close - open_p) / (open_p + 1e-8)
        
        # High volume ratio (>= 2.5x) + positive return (> 0.8%)
        sig = ((vol_ratio >= 2.5) & (price_ret >= 0.008)).astype(int)
        return sig


class StrategyV3_05_CrossAssetLeadLag:
    """EXP-V3-05: Cross-Asset Lead/Lag Predictive Model"""
    def __init__(self, btc_df: pd.DataFrame = None):
        self.exp_id = "EXP-V3-05"
        self.name = "Strategy E — Cross-Asset Lead/Lag"
        self.hypothesis = "Major leader (BTC) price momentum predicts subsequent altcoin follower moves."
        self.btc_df = btc_df

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        if symbol == "BTCUSDT" or self.btc_df is None or len(self.btc_df) < 20:
            # BTC doesn't trade against itself in lead/lag
            return pd.Series(0, index=df.index)
            
        # Strictly lagged BTC 6-bar return
        btc_close = self.btc_df["close"].reset_index(drop=True)
        btc_ret_6b = (btc_close - btc_close.shift(6)) / (btc_close.shift(6) + 1e-8)
        
        # Align index length with current asset df
        btc_ret_aligned = btc_ret_6b.reindex(df.index, fill_value=0.0)
        
        # Strong BTC momentum (> 2.5% over 6 hours) -> signal BUY on follower asset
        sig = (btc_ret_aligned > 0.025).astype(int)
        return sig


class StrategyV3_06_RegimeConditional:
    """EXP-V3-06: Regime-Conditional Strategy"""
    def __init__(self):
        self.exp_id = "EXP-V3-06"
        self.name = "Strategy F — Regime-Conditional Strategy"
        self.hypothesis = "Evaluating trend vs mean-reversion rules conditionally based on macro regime."

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        if len(df) < 60:
            return pd.Series(0, index=df.index)
            
        close = df["close"]
        high = df["high"]
        low = df["low"]
        
        # Compute ADX 14
        tr = np.maximum(high - low, np.maximum(np.abs(high - close.shift(1)), np.abs(low - close.shift(1))))
        atr = tr.rolling(14).mean()
        
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / (atr + 1e-8))
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / (atr + 1e-8))
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-8)
        adx = dx.rolling(14).mean()
        
        # Indicators
        ema50 = close.ewm(span=50, adjust=False).mean()
        
        # RSI 14
        delta = close.diff()
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        avg_gain = pd.Series(gain, index=df.index).ewm(span=14, adjust=False).mean()
        avg_loss = pd.Series(loss, index=df.index).ewm(span=14, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-8)
        rsi = 100 - (100 / (1 + rs))
        
        # Regime 1: Trending (ADX > 25) -> Breakout / EMA Trend
        trend_sig = (adx > 25) & (close > ema50) & (close.shift(1) <= ema50.shift(1))
        
        # Regime 2: Ranging (ADX <= 25) -> Oversold Mean Reversion (RSI < 28)
        range_sig = (adx <= 25) & (rsi < 28)
        
        sig = (trend_sig | range_sig).astype(int)
        return sig


class StrategyV3_07_ExtremeEventMeanReversion:
    """EXP-V3-07: Extreme Event Mean Reversion"""
    def __init__(self):
        self.exp_id = "EXP-V3-07"
        self.name = "Strategy G — Extreme Event Mean Reversion"
        self.hypothesis = "Extreme short-term price dislocations with high volume produce mean-reversion."

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        if len(df) < 50:
            return pd.Series(0, index=df.index)
            
        close = df["close"]
        vol = df["volume"]
        
        ema50 = close.ewm(span=50, adjust=False).mean()
        std50 = close.rolling(50).std()
        z_score = (close - ema50) / (std50 + 1e-8)
        
        vol_sma = vol.rolling(20).mean()
        vol_ratio = vol / (vol_sma + 1e-8)
        
        # Extreme negative dislocation (Z < -2.2) with high volume (>= 1.8x)
        sig = ((z_score < -2.2) & (vol_ratio >= 1.8)).astype(int)
        return sig


def get_all_v3_strategies(universe_candles: dict[str, list] = None) -> list:
    """Factory creating instances of all 7 V3 research strategy candidates."""
    btc_df = None
    if universe_candles and "BTCUSDT" in universe_candles:
        candles_btc = universe_candles["BTCUSDT"]
        if candles_btc and isinstance(candles_btc[0], (list, tuple)):
            btc_df = pd.DataFrame(candles_btc, columns=["ts", "open", "high", "low", "close", "volume"])
        else:
            btc_df = pd.DataFrame(candles_btc)
        
    return [
        StrategyV3_01_VolCompressionBreakout(),
        StrategyV3_02_FundingBasisRegime(),
        StrategyV3_03_OpenInterestPriceDivergence(),
        StrategyV3_04_VolumePriceImbalance(),
        StrategyV3_05_CrossAssetLeadLag(btc_df=btc_df),
        StrategyV3_06_RegimeConditional(),
        StrategyV3_07_ExtremeEventMeanReversion()
    ]
