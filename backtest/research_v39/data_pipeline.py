"""
Data Pipeline Module for NEXUS-7 Research V39
Manages real historical OHLCV loading, universe tier population,
and 50% Train, 30% Validation, and 20% Untouched Frozen Final Holdout splits.
"""

from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from backtest.research_v39.real_data_fetcher import fetch_real_ohlcv_data_v39
from backtest.research_v39.universe_builder import UNIVERSE_TIERS_V39, filter_point_in_time_liquidity_v39


def split_dataset_v39_holdout(
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


def load_universe_tier_v39(
    tier_name: str = "TIER_20",
    timeframe: str = "1h",
    days: int = 60,
    force_refresh: bool = False
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Dict[str, Any]]]:
    """
    Loads all real asset datasets for a specified universe tier.
    """
    symbols = UNIVERSE_TIERS_V39.get(tier_name, UNIVERSE_TIERS_V39["TIER_20"])
    datasets = {}
    metadata = {}

    for sym in symbols:
        df, meta = fetch_real_ohlcv_data_v39(symbol=sym, timeframe=timeframe, days=days, force_refresh=force_refresh)
        if df is not None and len(df) > 20:
            asset_key = sym.split("/")[0]
            datasets[asset_key] = df
            metadata[asset_key] = meta

    return datasets, metadata
