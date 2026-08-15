"""
Data Pipeline Module for NEXUS-7 Research V35
Manages 6 liquid universe tiers (20, 30, 50, 75, 100, 150 assets),
liquidity pre-filtering, 50/25/25 chronological partitioning, and rolling return correlations.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

UNIVERSE_TIERS = {
    "TIER_1": [f"COIN_{i:03d}" for i in range(1, 21)],    # 20 assets
    "TIER_2": [f"COIN_{i:03d}" for i in range(1, 31)],    # 30 assets
    "TIER_3": [f"COIN_{i:03d}" for i in range(1, 51)],    # 50 assets
    "TIER_4": [f"COIN_{i:03d}" for i in range(1, 76)],    # 75 assets
    "TIER_5": [f"COIN_{i:03d}" for i in range(1, 101)],   # 100 assets
    "TIER_6": [f"COIN_{i:03d}" for i in range(1, 151)]    # 150 assets
}

# Override top coins for realism
UNIVERSE_TIERS["TIER_1"][0] = "BTC"
UNIVERSE_TIERS["TIER_1"][1] = "ETH"
UNIVERSE_TIERS["TIER_1"][2] = "SOL"
UNIVERSE_TIERS["TIER_1"][3] = "AVAX"
UNIVERSE_TIERS["TIER_1"][4] = "BNB"


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


def apply_liquidity_filter(
    datasets: Dict[str, pd.DataFrame],
    min_avg_daily_volume: float = 1000000.0,
    max_zero_volume_pct: float = 0.05
) -> Tuple[Dict[str, pd.DataFrame], List[str], Dict[str, int]]:
    """Filters out low-volume, illiquid, or gapped assets."""
    eligible = {}
    rejected = []

    for asset, df in datasets.items():
        if len(df) < 50:
            rejected.append(asset)
            continue

        daily_vol = df["volume"].mean() * 24
        zero_vol_pct = (df["volume"] <= 0).mean()

        if daily_vol >= min_avg_daily_volume and zero_vol_pct <= max_zero_volume_pct:
            eligible[asset] = df
        else:
            rejected.append(asset)

    counts = {
        "UNIVERSE_SIZE": len(datasets),
        "TRADEABLE_UNIVERSE_SIZE": len(eligible),
        "REJECTED_UNIVERSE_SIZE": len(rejected)
    }
    return eligible, rejected, counts


def split_dataset_chronological(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits dataset into 50% Train/Calibration, 25% Validation, 25% Untouched OOS."""
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
    tier_name: str = "TIER_1",
    timeframe: str = "1h",
    num_bars: int = 300,
    seed: int = 42
) -> Dict[str, pd.DataFrame]:
    """Loads all asset datasets for a specified universe tier."""
    assets = UNIVERSE_TIERS.get(tier_name, UNIVERSE_TIERS["TIER_1"])
    datasets = {}
    for asset in assets:
        datasets[asset] = generate_synthetic_asset_data(asset, timeframe, num_bars=num_bars, seed=seed)
    return datasets


def compute_rolling_correlation_matrix(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Computes daily return correlation matrix across all assets in datasets."""
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
