"""
NEXUS-7 — RESEARCH V28 DATA PIPELINE
Loads multi-asset OHLCV data for 12 liquid pairs across 15m, 30m, 1h, and 4h timeframes.
Enforces strict 50% Train, 25% Validation, and 25% Untouched Out-of-Sample chronological splitting.
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List

SUPPORTED_PAIRS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
    "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT",
    "NEAR/USDT", "SUI/USDT"
]

TIMEFRAMES = ["15m", "30m", "1h", "4h"]

TF_MINUTES = {
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240
}


def generate_synthetic_ohlcv(symbol: str, timeframe: str = "30m", days: int = 180, seed: int = 42) -> pd.DataFrame:
    """Generates realistic synthetic OHLCV data with trend regimes, mean-reversion, and volatility clusters."""
    rng = np.random.RandomState(seed + sum(ord(c) for c in symbol) + TF_MINUTES[timeframe])
    mins = TF_MINUTES[timeframe]
    candles_per_day = int(1440 / mins)
    total_candles = candles_per_day * days

    start_time = pd.Timestamp("2026-01-01 00:00:00")
    timestamps = [start_time + pd.Timedelta(minutes=mins * i) for i in range(total_candles)]

    base_prices = {
        "BTC/USDT": 65000.0, "ETH/USDT": 3400.0, "SOL/USDT": 140.0,
        "BNB/USDT": 580.0, "XRP/USDT": 0.52, "DOGE/USDT": 0.12,
        "ADA/USDT": 0.45, "AVAX/USDT": 28.0, "LINK/USDT": 15.0,
        "DOT/USDT": 7.0, "NEAR/USDT": 5.5, "SUI/USDT": 1.2
    }
    initial_price = base_prices.get(symbol, 100.0)

    # Multi-regime drift + GARCH volatility clustering
    daily_vol = 0.025
    step_vol = daily_vol / np.sqrt(candles_per_day)

    returns = np.zeros(total_candles)
    current_vol = step_vol
    regime = 1.0  # 1.0 = uptrend, -1.0 = downtrend, 0.0 = ranging

    for i in range(1, total_candles):
        if i % (candles_per_day * 15) == 0:  # Switch regime every ~15 days
            regime = rng.choice([1.0, -1.0, 0.0], p=[0.4, 0.3, 0.3])

        # GARCH(1,1) vol update
        shocks = rng.normal(0, 1)
        current_vol = np.sqrt(0.000001 + 0.85 * (current_vol ** 2) + 0.10 * (shocks * current_vol) ** 2)
        drift = regime * 0.00015
        returns[i] = drift + shocks * current_vol

    price_path = initial_price * np.exp(np.cumsum(returns))

    close_prices = price_path
    high_prices = close_prices * (1.0 + np.abs(rng.normal(0.002, 0.0015, total_candles)))
    low_prices = close_prices * (1.0 - np.abs(rng.normal(0.002, 0.0015, total_candles)))
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = initial_price

    # Ensure Low <= Min(Open, Close) and High >= Max(Open, Close)
    real_high = np.maximum(high_prices, np.maximum(open_prices, close_prices))
    real_low = np.minimum(low_prices, np.minimum(open_prices, close_prices))

    volume = rng.lognormal(mean=10.0, sigma=0.5, size=total_candles)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": open_prices,
        "high": real_high,
        "low": real_low,
        "close": close_prices,
        "volume": volume
    })

    return df


def load_multi_asset_dataset(days: int = 180, seed: int = 42) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Loads OHLCV dataset for 12 liquid pairs across all timeframes."""
    dataset = {}
    for pair in SUPPORTED_PAIRS:
        dataset[pair] = {}
        for tf in TIMEFRAMES:
            df = generate_synthetic_ohlcv(symbol=pair, timeframe=tf, days=days, seed=seed)
            dataset[pair][tf] = df
    return dataset


def split_chronological_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits dataset into 50% Train, 25% Validation, and 25% Untouched Out-of-Sample slices."""
    n = len(df)
    train_end = int(n * 0.50)
    val_end = int(n * 0.75)

    df_train = df.iloc[:train_end].copy().reset_index(drop=True)
    df_val = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    df_oos = df.iloc[val_end:].copy().reset_index(drop=True)

    return df_train, df_val, df_oos
