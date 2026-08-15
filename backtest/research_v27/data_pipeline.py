"""
NEXUS-7 — RESEARCH V27 DATA PIPELINE
Multi-asset dataset loader for 12 liquid pairs across 15m, 30m, 1h, and 4h timeframes.
Applies strict chronological splitting: Train 50%, Validation 25%, Untouched Forward 25%.
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple
from backtest.research_v27.strategy_library import SUPPORTED_PAIRS, TIMEFRAMES


def generate_synthetic_ohlcv(symbol: str, timeframe: str, days: int = 180, seed: int = 42) -> pd.DataFrame:
    """
    Generates deterministic synthetic OHLCV market data for testing and offline execution.
    """
    tf_minutes = {"15m": 15, "30m": 30, "1h": 60, "4h": 240}.get(timeframe, 15)
    total_candles = int((days * 24 * 60) / tf_minutes)

    # Base price seeds per asset
    base_prices = {
        "BTC/USDT": 65000.0, "ETH/USDT": 3400.0, "SOL/USDT": 145.0,
        "BNB/USDT": 580.0, "XRP/USDT": 0.55, "DOGE/USDT": 0.12,
        "ADA/USDT": 0.38, "AVAX/USDT": 26.0, "LINK/USDT": 14.0,
        "DOT/USDT": 6.50, "NEAR/USDT": 4.80, "SUI/USDT": 1.25
    }
    start_price = base_prices.get(symbol, 100.0)

    # Unique random seed per symbol and timeframe
    sym_seed = seed + hash(f"{symbol}_{timeframe}") % 100000
    rng = np.random.RandomState(sym_seed)

    returns = rng.normal(0.0001, 0.008, total_candles)
    price_curve = start_price * np.exp(np.cumsum(returns))

    start_date = pd.Timestamp("2026-01-01 00:00:00")
    timestamps = [start_date + pd.Timedelta(minutes=i * tf_minutes) for i in range(total_candles)]

    highs = price_curve * (1 + rng.uniform(0.001, 0.006, total_candles))
    lows = price_curve * (1 - rng.uniform(0.001, 0.006, total_candles))
    opens = np.roll(price_curve, 1)
    opens[0] = start_price
    closes = price_curve
    volumes = rng.uniform(100.0, 5000.0, total_candles) * (start_price / 10.0)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes
    })

    return df


def load_multi_asset_dataset(days: int = 180, seed: int = 42) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Loads OHLCV datasets for all 12 liquid pairs across supported timeframes.
    Returns dict structure: dataset[symbol][timeframe] = DataFrame.
    """
    dataset = {}
    for pair in SUPPORTED_PAIRS:
        dataset[pair] = {}
        for tf in TIMEFRAMES:
            df = generate_synthetic_ohlcv(symbol=pair, timeframe=tf, days=days, seed=seed)
            dataset[pair][tf] = df
    return dataset


def split_chronological_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame strictly chronologically into:
    - Train: 50%
    - Validation: 25%
    - Untouched Forward Out-of-Sample: 25%
    """
    n = len(df)
    train_end = int(n * 0.50)
    val_end = int(n * 0.75)

    df_train = df.iloc[:train_end].copy().reset_index(drop=True)
    df_val = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    df_forward = df.iloc[val_end:].copy().reset_index(drop=True)

    return df_train, df_val, df_forward
