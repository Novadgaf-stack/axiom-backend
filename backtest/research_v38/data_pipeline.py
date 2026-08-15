"""
Data Pipeline Module for NEXUS-7 Research V38
Manages OHLCV dataset generation across 8 universe tiers,
supports multiple timeframes (5m, 15m, 30m, 1h, 4h; 1,000+ bars per asset),
50% Train, 30% Validation, and 20% Untouched Frozen Final Holdout splits.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from backtest.research_v38.universe_builder import UNIVERSE_TIERS


def generate_synthetic_asset_data_v38(
    symbol: str,
    timeframe: str = "1h",
    num_bars: int = 1000,
    seed: int = 42
) -> pd.DataFrame:
    """Generates synthetic OHLCV data with realistic drift and volatility."""
    symbol_hash = sum(ord(c) for c in symbol) + seed
    np.random.seed(symbol_hash % 2**32)

    freq_map = {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h"}
    freq_str = freq_map.get(timeframe, "1h")
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=num_bars, freq=freq_str)

    base_price = 50.0 + (symbol_hash % 200)
    volatility = 0.015 + (symbol_hash % 20) * 0.001
    drift = 0.0001 * (1 if symbol_hash % 2 == 0 else -1)

    returns = np.random.normal(drift, volatility, size=num_bars)
    price_paths = base_price * np.exp(np.cumsum(returns))

    opens = price_paths * (1.0 + np.random.normal(0, volatility * 0.2, size=num_bars))
    closes = price_paths
    highs = np.maximum(opens, closes) * (1.0 + np.abs(np.random.normal(0, volatility * 0.5, size=num_bars)))
    lows = np.minimum(opens, closes) * (1.0 - np.abs(np.random.normal(0, volatility * 0.5, size=num_bars)))
    volumes = np.random.uniform(500000.0, 5000000.0, size=num_bars)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "asset": symbol,
        "timeframe": timeframe
    })
    return validate_and_clean_ohlcv_v38(df)


def validate_and_clean_ohlcv_v38(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans OHLCV dataframe and handles NaNs/gaps."""
    df = df.copy()
    df = df.dropna(subset=["open", "high", "low", "close", "volume"])
    df = df[(df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)]
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df.sort_values("timestamp").reset_index(drop=True)


def split_dataset_v38_holdout(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits dataset into 50% Train, 30% Validation, 20% Untouched Frozen Final Holdout."""
    n = len(df)
    train_end = int(n * 0.50)
    val_end = int(n * 0.80)

    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    holdout_df = df.iloc[val_end:].copy().reset_index(drop=True)

    return train_df, val_df, holdout_df


def load_universe_tier_v38(
    tier_name: str = "TIER_20",
    timeframe: str = "1h",
    num_bars: int = 1000,
    seed: int = 42
) -> Dict[str, pd.DataFrame]:
    """Loads all asset datasets for a specified universe tier."""
    assets = UNIVERSE_TIERS.get(tier_name, UNIVERSE_TIERS["TIER_20"])
    datasets = {}
    for asset in assets:
        datasets[asset] = generate_synthetic_asset_data_v38(asset, timeframe, num_bars=num_bars, seed=seed)
    return datasets
