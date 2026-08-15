"""
Purged Validation Module for NEXUS-7 Final Master Research
Purged walk-forward validation with embargoing between train and test splits
to prevent overlapping trade/label leakage.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def apply_purged_embargo_split_final(
    df: pd.DataFrame,
    train_pct: float = 0.50,
    embargo_bars: int = 24
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Applies purged embargo window between train and test datasets.
    """
    n = len(df)
    train_end = int(n * train_pct)
    val_start = min(n, train_end + embargo_bars)

    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[val_start:].copy().reset_index(drop=True)

    return train_df, val_df
