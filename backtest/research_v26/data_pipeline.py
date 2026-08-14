"""
NEXUS-7 — RESEARCH V26 DATA PIPELINE
Strict chronological data splitting: Train (50%), Validation (25%), Untouched Forward (25%).
"""
import os
import random
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any

from backtest.data_source import fetch_binance_history, generate_synthetic_history
from backtest.research_v15.cost_aware import resample_candles
from backtest.research_v26.strategy_library import SUPPORTED_PAIRS


def prepare_dataframe(candles: list) -> pd.DataFrame:
    """Standardizes raw candle list into DataFrame with core indicators."""
    if not candles:
        return pd.DataFrame()

    if isinstance(candles[0], (list, tuple)):
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    else:
        df = pd.DataFrame(candles)

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)

    if pd.api.types.is_numeric_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["ema_fast"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=21, adjust=False).mean()
    df["ema_trend"] = df["close"].ewm(span=50, adjust=False).mean()

    tr = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs()
        )
    )
    df["atr"] = tr.rolling(window=14).mean().fillna(df["close"] * 0.01)

    return df


def load_multi_asset_dataset(days: int = 90, seed: int = 42, cache_dir: str = "data_cache") -> Dict[str, Dict[str, pd.DataFrame]]:
    """Loads candle feeds for 9 liquid pairs across 15m, 30m, 1h timeframes."""
    os.makedirs(cache_dir, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)

    dataset = {}
    for idx, sym in enumerate(SUPPORTED_PAIRS):
        pair_seed = seed + idx * 10
        c15_synth = generate_synthetic_history(days=days, timeframe_minutes=15, seed=pair_seed)
        c30_synth = resample_candles(c15_synth, factor=2)
        c1h_synth = resample_candles(c15_synth, factor=4)

        dataset[sym] = {
            "1h": prepare_dataframe(c1h_synth),
            "30m": prepare_dataframe(c30_synth),
            "15m": prepare_dataframe(c15_synth)
        }

    return dataset


def split_chronological_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame strictly chronologically:
    - Train (In-Sample): First 50%
    - Validation: Next 25%
    - Untouched Forward (Out-of-Sample): Final 25%
    """
    n = len(df)
    if n == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    n_train = int(n * 0.50)
    n_val = int(n * 0.25)

    df_train = df.iloc[:n_train].copy().reset_index(drop=True)
    df_val = df.iloc[n_train:n_train + n_val].copy().reset_index(drop=True)
    df_forward = df.iloc[n_train + n_val:].copy().reset_index(drop=True)

    return df_train, df_val, df_forward
