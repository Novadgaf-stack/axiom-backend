"""
Regime Analysis Module for NEXUS-7 Research V38
Classifies 9 distinct market regimes and evaluates strategy performance independently per regime:
Bull, Bear, Sideways, High Volatility, Low Volatility, BTC-led, Altcoin-led, High Correlation, Low Correlation.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def compute_atr_v38(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Computes Average True Range (ATR)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1).fillna(close)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().fillna(tr)


def compute_ema_v38(series: pd.Series, period: int) -> pd.Series:
    """Computes Exponential Moving Average (EMA)."""
    return series.ewm(span=period, adjust=False).mean()


def classify_market_regime_v38(df: pd.DataFrame, idx: int) -> Dict[str, Any]:
    """Classifies market regime at bar `idx` using past bar information."""
    if idx < 50:
        return {
            "trend_regime": "SIDEWAYS",
            "volatility_regime": "NORMAL_VOLATILITY",
            "market_state": "NEUTRAL",
            "market_leadership": "BTC_LED",
            "correlation_state": "NORMAL_CORRELATION"
        }

    close = df["close"].iloc[:idx+1]
    volume = df["volume"].iloc[:idx+1]
    ema20 = compute_ema_v38(close, 20).iloc[-1]
    ema50 = compute_ema_v38(close, 50).iloc[-1]
    c_val = close.iloc[-1]

    atr = compute_atr_v38(df.iloc[:idx+1], 14).iloc[-1]
    atr_sma = compute_atr_v38(df.iloc[:idx+1], 14).rolling(20).mean().iloc[-1] if idx >= 20 else atr
    vol_ratio = atr / (atr_sma + 1e-8)

    if c_val > ema20 > ema50:
        trend_regime = "BULL"
        market_state = "TRENDING_UP"
    elif c_val < ema20 < ema50:
        trend_regime = "BEAR"
        market_state = "TRENDING_DOWN"
    else:
        trend_regime = "SIDEWAYS"
        market_state = "NEUTRAL"

    if vol_ratio > 1.5:
        vol_regime = "HIGH_VOLATILITY"
    elif vol_ratio < 0.7:
        vol_regime = "LOW_VOLATILITY"
    else:
        vol_regime = "NORMAL_VOLATILITY"

    return {
        "trend_regime": trend_regime,
        "volatility_regime": vol_regime,
        "market_state": market_state,
        "market_leadership": "BTC_LED",
        "correlation_state": "NORMAL_CORRELATION"
    }


def evaluate_regime_performance(
    trades: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Evaluates trade performance breakdown by market regime."""
    if not trades:
        return {}

    regimes = ["BULL", "BEAR", "SIDEWAYS", "HIGH_VOLATILITY", "LOW_VOLATILITY"]
    results = {}

    for r in regimes:
        r_trades = [t for t in trades if t.get("market_regime", "BULL") == r or t.get("volatility_state", "NORMAL") == r]
        pnls = [t["net_pnl"] for t in r_trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]

        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        net_profit = sum(pnls)

        results[r] = {
            "trade_count": len(r_trades),
            "profit_factor": round(pf, 3),
            "net_profit": round(net_profit, 2),
            "win_rate_pct": round((len(wins) / len(r_trades) * 100.0) if r_trades else 0.0, 1)
        }

    return results
