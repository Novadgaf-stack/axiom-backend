"""
NEXUS-7 Research V30 — Multi-Asset Data Pipeline Module
Provides synthetic/historical multi-asset OHLCV dataset generator across
12 liquid crypto pairs and 4 timeframes with strict 50/25/25 chronological splits,
rolling return correlation matrices, and asset holdout split functionality.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

SUPPORTED_ASSETS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE",
    "ADA", "AVAX", "LINK", "DOT", "NEAR", "SUI"
]

SUPPORTED_TIMEFRAMES = ["15m", "30m", "1h", "4h"]

TF_BARS_PER_DAY = {
    "15m": 96,
    "30m": 48,
    "1h": 24,
    "4h": 6,
}


def generate_synthetic_asset_data(
    asset: str,
    timeframe: str,
    num_bars: int = 4000,
    seed: int = 42
) -> pd.DataFrame:
    """Generates realistic synthetic OHLCV data for a single asset/timeframe."""
    asset_seed = seed + sum(ord(c) for c in asset) + TF_BARS_PER_DAY.get(timeframe, 24)
    rng = np.random.default_rng(asset_seed)

    base_prices = {
        "BTC": 65000.0, "ETH": 3500.0, "SOL": 145.0, "BNB": 580.0,
        "XRP": 0.55, "DOGE": 0.12, "ADA": 0.40, "AVAX": 28.0,
        "LINK": 14.0, "DOT": 6.50, "NEAR": 4.80, "SUI": 1.25
    }
    start_price = base_prices.get(asset, 100.0)

    # Volatility scale per bar
    vol_scale = {
        "15m": 0.004,
        "30m": 0.006,
        "1h": 0.009,
        "4h": 0.018,
    }.get(timeframe, 0.008)

    # Beta relative to market trend
    asset_beta = {
        "BTC": 0.8, "ETH": 1.0, "SOL": 1.3, "BNB": 0.9,
        "XRP": 1.2, "DOGE": 1.5, "ADA": 1.2, "AVAX": 1.4,
        "LINK": 1.1, "DOT": 1.2, "NEAR": 1.3, "SUI": 1.4
    }.get(asset, 1.0)

    # Generate log returns with macro regime shifts
    raw_returns = rng.normal(0, vol_scale * asset_beta, size=num_bars)

    regime_length = 350
    for i in range(0, num_bars, regime_length):
        regime_drift = rng.uniform(-0.0004, 0.0004)
        end_idx = min(i + regime_length, num_bars)
        raw_returns[i:end_idx] += regime_drift

    price_path = start_price * np.exp(np.cumsum(raw_returns))

    highs = price_path * (1.0 + np.abs(rng.normal(0, vol_scale * 0.7, num_bars)))
    lows = price_path * (1.0 - np.abs(rng.normal(0, vol_scale * 0.7, num_bars)))
    opens = np.roll(price_path, 1)
    opens[0] = start_price
    closes = price_path

    highs = np.maximum(highs, np.maximum(opens, closes))
    lows = np.minimum(lows, np.minimum(opens, closes))

    volumes = rng.lognormal(mean=10.0, sigma=0.8, size=num_bars)

    freq_map = {"15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h"}
    pd_freq = freq_map.get(timeframe, timeframe)
    dates = pd.date_range(end="2026-08-01", periods=num_bars, freq=pd_freq)

    df = pd.DataFrame({
        "timestamp": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "asset": asset,
        "timeframe": timeframe
    })
    return df


def split_dataset_chronological(
    df: pd.DataFrame,
    train_ratio: float = 0.50,
    val_ratio: float = 0.25,
    oos_ratio: float = 0.25
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits dataset into 50% Train, 25% Validation, and 25% Untouched OOS."""
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    oos_df = df.iloc[val_end:].copy().reset_index(drop=True)

    return train_df, val_df, oos_df


def compute_asset_correlation_matrix(
    asset_data: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Computes return correlation matrix across all assets."""
    returns_dict = {}
    for asset, df in asset_data.items():
        if "close" in df.columns:
            returns_dict[asset] = df["close"].pct_change().dropna().values

    min_len = min(len(r) for r in returns_dict.values())
    trimmed_returns = {k: v[-min_len:] for k, v in returns_dict.items()}

    ret_df = pd.DataFrame(trimmed_returns)
    return ret_df.corr()


def get_asset_holdout_split(
    assets: List[str] = None,
    holdout_ratio: float = 0.25,
    seed: int = 42
) -> Tuple[List[str], List[str]]:
    """Splits supported assets into training assets and holdout assets."""
    if assets is None:
        assets = SUPPORTED_ASSETS.copy()

    rng = np.random.default_rng(seed)
    shuffled = assets.copy()
    rng.shuffle(shuffled)

    num_holdout = max(1, int(len(assets) * holdout_ratio))
    holdout_assets = shuffled[:num_holdout]
    train_assets = shuffled[num_holdout:]

    return train_assets, holdout_assets


def load_multi_asset_dataset(
    assets: List[str] = None,
    timeframes: List[str] = None,
    num_bars: int = 4000,
    seed: int = 42
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Loads multi-asset multi-timeframe dataset.
    Returns nested dict: dataset[asset][timeframe] = DataFrame
    """
    if assets is None:
        assets = SUPPORTED_ASSETS
    if timeframes is None:
        timeframes = SUPPORTED_TIMEFRAMES

    dataset = {}
    for asset in assets:
        dataset[asset] = {}
        for tf in timeframes:
            dataset[asset][tf] = generate_synthetic_asset_data(
                asset=asset,
                timeframe=tf,
                num_bars=num_bars,
                seed=seed
            )
    return dataset
