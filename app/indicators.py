"""
Technical indicators computed from OHLCV candles. These serve two purposes:
1. Provide a quantitative "technical bias" that must AGREE with Gemini's
   directional call before any trade is allowed (see strategy.py).
2. Supply ATR for volatility-scaled stop-loss / take-profit sizing (risk.py).
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class TechnicalSnapshot:
    close: float
    ema_fast: float
    ema_slow: float
    ema_50: float
    rsi: float
    atr: float
    macd: float
    macd_signal: float
    volume_ratio: float  # last volume / avg volume
    adx: float
    bias: str  # "LONG", "SHORT", "NEUTRAL"

    def to_prompt_dict(self) -> dict:
        return {
            "close": round(self.close, 6),
            "ema_fast_9": round(self.ema_fast, 6),
            "ema_slow_21": round(self.ema_slow, 6),
            "ema_50": round(self.ema_50, 6),
            "rsi_14": round(self.rsi, 2),
            "atr_14": round(self.atr, 6),
            "adx_14": round(self.adx, 2),
            "macd": round(self.macd, 6),
            "macd_signal": round(self.macd_signal, 6),
            "volume_ratio_vs_avg": round(self.volume_ratio, 2),
            "technical_bias": self.bias,
        }


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period).mean()


def _adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = _atr(df, period=1)
    tr_smooth = tr.rolling(period).sum()

    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).sum() / tr_smooth.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).sum() / tr_smooth.replace(0, np.nan))

    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.rolling(period).mean()
    return adx.fillna(0.0)


def compute_snapshot(
    ohlcv: list, atr_period: int = 14, min_volume_ratio: float = 0.0, min_adx: float = 20.0
) -> TechnicalSnapshot | None:
    """
    ohlcv: list of [timestamp, open, high, low, close, volume] from ccxt.fetch_ohlcv

    IMPORTANT: ccxt's last returned candle is the currently-forming one (it
    updates every call until the period closes). Computing signals off a
    half-formed candle is a classic source of noisy, flip-flopping false
    signals — the RSI/MACD/EMA values can look completely different a minute
    later purely because the candle isn't finished. We drop it and compute
    off the last *closed* candle only.
    """
    if isinstance(ohlcv, pd.DataFrame):
        df = ohlcv.iloc[:-1]
    else:
        closed_candles = ohlcv[:-1]  # drop the still-forming candle
        df = pd.DataFrame(closed_candles, columns=["ts", "open", "high", "low", "close", "volume"])

    ema_fast = _ema(df["close"], 9)
    ema_slow = _ema(df["close"], 21)
    ema_50 = _ema(df["close"], 50)
    rsi = _rsi(df["close"], 14)
    atr = _atr(df, atr_period)
    adx_series = _adx(df, 14)
    macd_line = ema_fast - ema_slow
    macd_signal = _ema(macd_line, 9)

    last_close = float(df["close"].iloc[-1])
    last_ema_fast = float(ema_fast.iloc[-1])
    last_ema_slow = float(ema_slow.iloc[-1])
    last_ema_50 = float(ema_50.iloc[-1])
    last_rsi = float(rsi.iloc[-1])
    last_atr = float(atr.iloc[-1]) if not np.isnan(atr.iloc[-1]) else 0.0
    last_adx = float(adx_series.iloc[-1]) if not np.isnan(adx_series.iloc[-1]) else 0.0
    last_macd = float(macd_line.iloc[-1])
    last_macd_signal = float(macd_signal.iloc[-1])
    avg_volume = float(df["volume"].tail(20).mean()) or 1e-9
    last_volume = float(df["volume"].iloc[-1])
    volume_ratio = last_volume / avg_volume

    bias = "NEUTRAL"
    volume_ok = volume_ratio >= min_volume_ratio
    adx_ok = last_adx >= min_adx
    bullish = (
        last_ema_fast > last_ema_slow
        and last_close > last_ema_50
        and last_macd > last_macd_signal
        and 45 <= last_rsi <= 68
        and volume_ok
        and adx_ok
    )
    bearish = (
        last_ema_fast < last_ema_slow
        and last_close < last_ema_50
        and last_macd < last_macd_signal
        and 32 <= last_rsi <= 55
        and volume_ok
        and adx_ok
    )
    if bullish:
        bias = "LONG"
    elif bearish:
        bias = "SHORT"

    return TechnicalSnapshot(
        close=last_close,
        ema_fast=last_ema_fast,
        ema_slow=last_ema_slow,
        ema_50=last_ema_50,
        rsi=last_rsi,
        atr=last_atr,
        macd=last_macd,
        macd_signal=last_macd_signal,
        volume_ratio=volume_ratio,
        adx=last_adx,
        bias=bias,
    )
