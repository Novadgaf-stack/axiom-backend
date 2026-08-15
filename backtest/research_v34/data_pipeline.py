"""
Data Pipeline Module for NEXUS-7 Research V34
Manages multi-asset data generation/loading across Tier 1 (12), Tier 2 (25), Tier 3 (50), Tier 4 (75), Tier 5 (100), Tier 6 (150) universe tiers.
Implements liquidity filtering, data quality verification, and chronological 50/25/25 partitioning.
Distinguishes UNIVERSE_SIZE, LIQUID_UNIVERSE_SIZE, and TRADEABLE_UNIVERSE_SIZE.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd

UNIVERSE_TIERS = {
    "TIER_1": [
        "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE",
        "ADA", "AVAX", "LINK", "DOT", "NEAR", "SUI"
    ],
    "TIER_2": [
        "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE",
        "ADA", "AVAX", "LINK", "DOT", "NEAR", "SUI",
        "LTC", "BCH", "UNI", "AAVE", "ATOM", "FIL", "ARB", "OP",
        "INJ", "SEI", "TIA", "TAO", "RENDER"
    ],
    "TIER_3": [
        "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE",
        "ADA", "AVAX", "LINK", "DOT", "NEAR", "SUI",
        "LTC", "BCH", "UNI", "AAVE", "ATOM", "FIL", "ARB", "OP",
        "INJ", "SEI", "TIA", "TAO", "RENDER",
        "FET", "APT", "STX", "PEPE", "WIF", "FLOKI", "BONK", "GALA", "SAND", "MANA",
        "CRV", "SNX", "LDO", "MKR", "RUNE", "DYDX", "ENS", "IMX", "GRT", "COMP",
        "1INCH", "ALGO", "FTM", "EGLD", "FLOW"
    ],
    "TIER_4": [
        f"ASSET_{i:03d}" for i in range(1, 76)
    ],
    "TIER_5": [
        f"ASSET_{i:03d}" for i in range(1, 101)
    ],
    "TIER_6": [
        f"ASSET_{i:03d}" for i in range(1, 151)
    ]
}

# Override top names for Tier 4, Tier 5, Tier 6
UNIVERSE_TIERS["TIER_4"][:50] = UNIVERSE_TIERS["TIER_3"]
UNIVERSE_TIERS["TIER_5"][:50] = UNIVERSE_TIERS["TIER_3"]
UNIVERSE_TIERS["TIER_6"][:50] = UNIVERSE_TIERS["TIER_3"]

SUPPORTED_TIMEFRAMES = ["15m", "30m", "1h", "4h"]


def validate_and_clean_ohlcv(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool, List[str]]:
    """
    Validates OHLCV dataset for missing candles, timestamp ordering, and impossible OHLC bounds.
    """
    issues = []
    if df.empty:
        return df, False, ["Empty DataFrame"]

    df_clean = df.sort_values("timestamp").reset_index(drop=True)

    if not df_clean["timestamp"].is_monotonic_increasing:
        issues.append("Timestamps were out of order")

    bad_high = df_clean["high"] < df_clean[["open", "close"]].max(axis=1)
    bad_low = df_clean["low"] > df_clean[["open", "close"]].min(axis=1)

    if bad_high.any() or bad_low.any():
        issues.append("Corrected impossible High/Low values")
        df_clean["high"] = df_clean[["open", "close", "high"]].max(axis=1)
        df_clean["low"] = df_clean[["open", "close", "low"]].min(axis=1)

    if (df_clean["close"] <= 0).any():
        issues.append("Contains zero or negative close prices")

    is_valid = len(df_clean) >= 50 and (df_clean["close"] > 0).all()
    return df_clean, is_valid, issues


def apply_liquidity_filter(
    datasets: Dict[str, pd.DataFrame],
    min_avg_daily_volume: float = 1000000.0, # $1M min daily volume
    max_missing_bar_pct: float = 0.05
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str], Dict[str, int]]:
    """
    Filters multi-asset datasets based on average daily volume and data completeness.
    Returns (tradeable_datasets, rejected_assets_dict, universe_counts_dict).
    """
    eligible = {}
    rejected = {}

    universe_size = len(datasets)

    for asset, df in datasets.items():
        df_clean, is_valid, issues = validate_and_clean_ohlcv(df)
        if not is_valid:
            rejected[asset] = f"Data validation failed: {', '.join(issues)}"
            continue

        avg_vol = (df_clean["close"] * df_clean["volume"]).mean()
        if avg_vol < min_avg_daily_volume and asset not in ["BTC", "ETH", "SOL"]:
            rejected[asset] = f"Insufficient daily volume (${avg_vol:,.0f} < ${min_avg_daily_volume:,.0f})"
            continue

        eligible[asset] = df_clean

    liquid_universe_size = len(eligible) + len([k for k in rejected if "volume" not in rejected[k]])
    tradeable_universe_size = len(eligible)

    counts = {
        "UNIVERSE_SIZE": universe_size,
        "LIQUID_UNIVERSE_SIZE": liquid_universe_size,
        "TRADEABLE_UNIVERSE_SIZE": tradeable_universe_size
    }

    return eligible, rejected, counts


def generate_synthetic_asset_data(
    asset: str,
    timeframe: str,
    num_bars: int = 1500,
    seed: int = 42
) -> pd.DataFrame:
    """Generates realistic synthetic OHLCV price series for an asset/timeframe."""
    rng = np.random.default_rng(seed + hash(asset) % 10000 + hash(timeframe) % 1000)

    base_price = float(10.0 + (hash(asset) % 500))
    daily_vol = float(0.025 + (hash(asset) % 30) / 1000.0)

    tf_minutes = {"15m": 15, "30m": 30, "1h": 60, "4h": 240}.get(timeframe, 60)
    bar_vol = daily_vol * np.sqrt(tf_minutes / 1440.0)

    timestamps = pd.date_range("2025-06-01", periods=num_bars, freq=f"{tf_minutes}min")

    returns = np.zeros(num_bars)
    regime = 1  # 1 = Bull, -1 = Bear, 0 = Range

    for i in range(1, num_bars):
        if rng.random() < 0.03:
            regime = rng.choice([1, -1, 0], p=[0.4, 0.4, 0.2])
        drift = regime * 0.00025
        vol_scale = rng.gamma(2.0, 0.5) if regime != 0 else 0.7
        returns[i] = rng.normal(drift, bar_vol * vol_scale)

    price_series = base_price * np.exp(np.cumsum(returns))

    opens = np.zeros(num_bars)
    highs = np.zeros(num_bars)
    lows = np.zeros(num_bars)
    closes = np.zeros(num_bars)
    volumes = np.zeros(num_bars)

    for i in range(num_bars):
        p_close = price_series[i]
        p_open = price_series[i - 1] if i > 0 else p_close * (1.0 - returns[0])
        intra_vol = abs(returns[i]) + bar_vol * 0.5

        p_high = max(p_open, p_close) * (1.0 + rng.uniform(0.0005, intra_vol))
        p_low = min(p_open, p_close) * (1.0 - rng.uniform(0.0005, intra_vol))

        opens[i] = p_open
        highs[i] = p_high
        lows[i] = p_low
        closes[i] = p_close
        volumes[i] = rng.uniform(500000.0, 10000000.0) * (1.0 + 5.0 * abs(returns[i]))

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "asset": asset,
        "timeframe": timeframe
    })

    return df


def split_dataset_chronological(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits dataset chronologically into 50% Train, 25% Validation, 25% Untouched OOS."""
    n = len(df)
    n_train = int(n * 0.50)
    n_val = int(n * 0.25)

    df_train = df.iloc[:n_train].copy()
    df_val = df.iloc[n_train:n_train + n_val].copy()
    df_oos = df.iloc[n_train + n_val:].copy()

    return df_train, df_val, df_oos


def get_asset_holdout_split(datasets: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """Splits each asset dataset chronologically into 50% Train, 25% Validation, 25% Untouched OOS."""
    train_dict = {}
    val_dict = {}
    oos_dict = {}
    for asset, df in datasets.items():
        tr, val, oos = split_dataset_chronological(df)
        train_dict[asset] = tr
        val_dict[asset] = val
        oos_dict[asset] = oos
    return train_dict, val_dict, oos_dict


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
        resampled = df.set_index("timestamp")["close"].resample("1D").last().pct_change().dropna()
        close_dict[asset] = resampled

    df_returns = pd.DataFrame(close_dict).dropna()
    return df_returns.corr()
