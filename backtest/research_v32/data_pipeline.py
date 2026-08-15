"""
Data Pipeline Module for NEXUS-7 Research V32
Manages multi-asset data generation/loading, chronological 50/25/25 partitioning,
and asset correlation calculations for exposure caps.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

SUPPORTED_ASSETS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE",
    "ADA", "AVAX", "LINK", "DOT", "NEAR", "SUI"
]

SUPPORTED_TIMEFRAMES = ["15m", "30m", "1h", "4h"]


def generate_synthetic_asset_data(
    asset: str,
    timeframe: str,
    num_bars: int = 1500,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates realistic synthetic OHLCV price series for a given asset and timeframe.
    Uses geometric Brownian motion with regime switching and stochastic volatility.
    """
    rng = np.random.default_rng(seed + hash(asset) % 10000 + hash(timeframe) % 1000)

    # Base price & volatility profiles per asset
    asset_props = {
        "BTC": (65000.0, 0.025),
        "ETH": (3400.0, 0.030),
        "SOL": (145.0, 0.040),
        "BNB": (580.0, 0.028),
        "XRP": (0.58, 0.035),
        "DOGE": (0.12, 0.045),
        "ADA": (0.38, 0.038),
        "AVAX": (24.0, 0.042),
        "LINK": (12.5, 0.036),
        "DOT": (4.5, 0.039),
        "NEAR": (4.2, 0.044),
        "SUI": (1.1, 0.048)
    }

    base_price, daily_vol = asset_props.get(asset, (100.0, 0.035))

    tf_minutes = {
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240
    }.get(timeframe, 60)

    # Convert daily vol to timeframe vol
    bar_vol = daily_vol * np.sqrt(tf_minutes / 1440.0)

    timestamps = pd.date_range("2025-06-01", periods=num_bars, freq=f"{tf_minutes}min")

    returns = np.zeros(num_bars)
    regime = 1  # 1 = Bull/Trending, -1 = Bear/Pullback, 0 = Ranging

    for i in range(1, num_bars):
        if rng.random() < 0.03: # Regime switch probability
            regime = rng.choice([1, -1, 0], p=[0.4, 0.4, 0.2])

        drift = regime * 0.0002
        vol_scale = rng.gamma(2.0, 0.5) if regime != 0 else 0.7
        r = rng.normal(drift, bar_vol * vol_scale)
        returns[i] = r

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
        volumes[i] = rng.uniform(100000.0, 5000000.0) * (1.0 + 5.0 * abs(returns[i]))

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
    """
    Splits dataset chronologically into:
    - 50% Train
    - 25% Validation
    - 25% Untouched OOS
    """
    n = len(df)
    n_train = int(n * 0.50)
    n_val = int(n * 0.25)

    df_train = df.iloc[:n_train].copy()
    df_val = df.iloc[n_train:n_train + n_val].copy()
    df_oos = df.iloc[n_train + n_val:].copy()

    return df_train, df_val, df_oos


def load_multi_asset_dataset(
    assets: List[str] = SUPPORTED_ASSETS,
    timeframe: str = "1h",
    num_bars: int = 1500,
    seed: int = 42
) -> Dict[str, pd.DataFrame]:
    """Loads datasets for multiple assets for a specific timeframe."""
    datasets = {}
    for asset in assets:
        datasets[asset] = generate_synthetic_asset_data(asset, timeframe, num_bars=num_bars, seed=seed)
    return datasets


def compute_asset_correlation_matrix(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Computes daily price return correlation matrix across multi-asset datasets."""
    close_dict = {}
    for asset, df in datasets.items():
        resampled = df.set_index("timestamp")["close"].resample("1D").last().pct_change().dropna()
        close_dict[asset] = resampled

    df_returns = pd.DataFrame(close_dict).dropna()
    return df_returns.corr()


def get_asset_holdout_split(
    datasets: Dict[str, pd.DataFrame]
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """Splits all multi-asset datasets into Train, Validation, and Untouched OOS subsets."""
    train_dict, val_dict, oos_dict = {}, {}, {}
    for asset, df in datasets.items():
        d_tr, d_va, d_oo = split_dataset_chronological(df)
        train_dict[asset] = d_tr
        val_dict[asset] = d_va
        oos_dict[asset] = d_oo
    return train_dict, val_dict, oos_dict
