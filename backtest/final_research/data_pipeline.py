"""
Data Pipeline Module for NEXUS-7 Final Master Research
Manages real historical OHLCV loading, universe tier population,
and 50% Train, 30% Validation, and 20% Untouched Frozen Final Holdout splits.
"""

from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from backtest.final_research.real_data_engine import fetch_real_ohlcv_data_final
from backtest.final_research.universe import UNIVERSE_TIERS_FINAL, filter_point_in_time_liquidity_final


def split_dataset_final_holdout(
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


def load_universe_tier_final(
    tier_name: str = "TIER_20",
    timeframe: str = "1h",
    days: int = 60,
    force_refresh: bool = False
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Dict[str, Any]]]:
    """
    Loads all real asset datasets for a specified universe tier.
    """
    symbols = UNIVERSE_TIERS_FINAL.get(tier_name, UNIVERSE_TIERS_FINAL["TIER_20"])
    datasets = {}
    metadata = {}

    for sym in symbols:
        df, meta = fetch_real_ohlcv_data_final(symbol=sym, timeframe=timeframe, days=days, force_refresh=force_refresh)
        if df is not None and len(df) > 20:
            asset_key = sym.split("/")[0]
            datasets[asset_key] = df
            metadata[asset_key] = meta

    return datasets, metadata
