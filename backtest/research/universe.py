"""
Multi-Asset Historical Universe Manager for NEXUS-7 Engine.
Manages OHLCV historical data loading, resampling, and caching for:
BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, XRP/USDT
"""
import os
import time
from typing import Dict, List, Tuple
import pandas as pd

# Supported multi-asset research universe
RESEARCH_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]


def load_asset_df(data_dir: str, symbol: str, timeframe: str = "1h") -> pd.DataFrame:
    """
    Loads OHLCV DataFrame for a given symbol and timeframe.
    Standardizes timestamp column to 'ts'.
    """
    symbol_clean = symbol.replace("/", "").replace(":", "")
    # Check for direct timeframe match
    pattern = f"{symbol_clean}_{timeframe}_"
    files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith(".csv")]

    if files:
        filepath = os.path.join(data_dir, files[0])
        df = pd.read_csv(filepath)
        if "timestamp" in df.columns:
            df = df.rename(columns={"timestamp": "ts"})
        return df

    # Fallback to 15m resample if 1h/4h requested
    files_15m = [f for f in os.listdir(data_dir) if f.startswith(f"{symbol_clean}_15m_") and f.endswith(".csv")]
    if files_15m:
        filepath = os.path.join(data_dir, files_15m[0])
        df_15m = pd.read_csv(filepath)
        if "timestamp" in df_15m.columns:
            df_15m = df_15m.rename(columns={"timestamp": "ts"})
        
        dt_idx = pd.to_datetime(df_15m["ts"], unit="ms", utc=True)
        rule = "1h" if timeframe == "1h" else ("4h" if timeframe == "4h" else "15min")
        df_resampled = df_15m.set_index(dt_idx).resample(rule).agg({
            "ts": "first",
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna().reset_index(drop=True)
        return df_resampled

    # Synthetic fallback generator for testing if offline/missing asset
    return _generate_synthetic_ohlcv(symbol, timeframe)


def _generate_synthetic_ohlcv(symbol: str, timeframe: str = "1h") -> pd.DataFrame:
    """
    Generates realistic synthetic OHLCV data if historical CSV is missing for a pair.
    """
    import numpy as np
    np.random.seed(abs(hash(symbol)) % 10000)
    
    num_bars = 8760 if timeframe in ["1h", "1H"] else 2190
    start_ms = 1754866800000
    ms_step = 3600000 if timeframe in ["1h", "1H"] else 14400000

    base_price = {"SOLUSDT": 180.0, "BNBUSDT": 600.0, "XRPUSDT": 2.50}.get(symbol, 100.0)
    returns = np.random.normal(0.0001, 0.015, size=num_bars)
    price_series = base_price * np.exp(np.cumsum(returns))

    rows = []
    curr_ts = start_ms
    for i in range(num_bars):
        close_p = float(price_series[i])
        high_p = close_p * (1.0 + abs(np.random.normal(0, 0.005)))
        low_p = close_p * (1.0 - abs(np.random.normal(0, 0.005)))
        open_p = (high_p + low_p) / 2.0
        vol = float(np.random.exponential(1000.0))
        rows.append({
            "ts": curr_ts,
            "open": round(open_p, 4),
            "high": round(high_p, 4),
            "low": round(low_p, 4),
            "close": round(close_p, 4),
            "volume": round(vol, 2),
        })
        curr_ts += ms_step

    return pd.DataFrame(rows)


def load_universe_datasets(data_dir: str, timeframe: str = "1h") -> Dict[str, List[list]]:
    """
    Loads OHLCV candle lists [ts, open, high, low, close, volume] for all universe assets.
    """
    universe = {}
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    for pair in RESEARCH_PAIRS:
        df = load_asset_df(data_dir, pair, timeframe)
        candles = df[["ts", "open", "high", "low", "close", "volume"]].values.tolist()
        universe[pair] = candles

    return universe
