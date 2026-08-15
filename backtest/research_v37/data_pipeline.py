"""
Data Pipeline Module for NEXUS-7 Research V37
Manages OHLCV dataset generation across 6 universe tiers,
supports multiple timeframes (15m, 30m, 1h, 4h), 50/25/25 chronological splits,
and rolling correlation matrices.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from backtest.research_v37.universe import UNIVERSE_TIERS


def generate_synthetic_asset_data(
    symbol: str,
    timeframe: str = "1h",
    num_bars: int = 1500,
    seed: int = 42
) -> pd.DataFrame:
    """Generates synthetic OHLCV data with realistic drift and volatility."""
    symbol_hash = sum(ord(c) for c in symbol) + seed
    np.random.seed(symbol_hash % 2**32)

    freq_map = {"15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h"}
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
    return validate_and_clean_ohlcv(df)


def validate_and_clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans OHLCV dataframe and handles NaNs/gaps."""
    df = df.copy()
    df = df.dropna(subset=["open", "high", "low", "close", "volume"])
    df = df[(df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)]
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df.sort_values("timestamp").reset_index(drop=True)


def split_dataset_chronological(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits dataset into 50% Train, 25% Validation, 25% Untouched Locked OOS."""
    n = len(df)
    train_end = int(n * 0.50)
    val_end = int(n * 0.75)

    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    oos_df = df.iloc[val_end:].copy().reset_index(drop=True)

    return train_df, val_df, oos_df


def get_asset_holdout_split(
    datasets: Dict[str, pd.DataFrame]
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """Applies 50/25/25 chronological split across all assets in datasets."""
    tr_dict, val_dict, oos_dict = {}, {}, {}
    for asset, df in datasets.items():
        tr, val, oos = split_dataset_chronological(df)
        tr_dict[asset] = tr
        val_dict[asset] = val
        oos_dict[asset] = oos
    return tr_dict, val_dict, oos_dict


def load_universe_tier(
    tier_name: str = "TIER_A_20",
    timeframe: str = "1h",
    num_bars: int = 400,
    seed: int = 42
) -> Dict[str, pd.DataFrame]:
    """Loads all asset datasets for a specified universe tier."""
    assets = UNIVERSE_TIERS.get(tier_name, UNIVERSE_TIERS["TIER_A_20"])
    datasets = {}
    for asset in assets:
        datasets[asset] = generate_synthetic_asset_data(asset, timeframe, num_bars=num_bars, seed=seed)
    return datasets


def compute_rolling_correlation_matrix(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Computes daily return correlation matrix across all assets in datasets using past returns."""
    close_dict = {}
    for asset, df in datasets.items():
        if len(df) > 0:
            close_dict[asset] = df["close"].values

    if not close_dict:
        return pd.DataFrame()

    min_len = min(len(v) for v in close_dict.values())
    price_df = pd.DataFrame({k: v[:min_len] for k, v in close_dict.items()})
    returns_df = price_df.pct_change().fillna(0.0)
    return returns_df.corr().abs().fillna(0.0)
