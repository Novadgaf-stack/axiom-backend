"""
NEXUS-7 — PURGED & EMBARGOED CROSS-VALIDATION (RESEARCH V5)
Eliminates overlapping label leakage between training and validation samples.
"""
from typing import Dict, List, Tuple
import numpy as np


class PurgedCrossValidator:
    """Implements Purged & Embargoed K-Fold split logic for non-overlapping validation."""

    def __init__(self, n_splits: int = 5, pct_embargo: float = 0.02, max_hold_bars: int = 48):
        self.n_splits = n_splits
        self.pct_embargo = pct_embargo
        self.max_hold_bars = max_hold_bars

    def split(self, n_samples: int) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Yields (train_indices, test_indices) pairs with purging & embargoing.
        """
        indices = np.arange(n_samples)
        fold_size = n_samples // self.n_splits
        embargo_size = int(n_samples * self.pct_embargo)
        splits = []

        for i in range(self.n_splits):
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < self.n_splits - 1 else n_samples

            test_idx = indices[test_start:test_end]

            # Purge: remove training samples whose labels overlap into test set
            purge_start = max(0, test_start - self.max_hold_bars)
            # Embargo: remove training samples immediately following test set
            embargo_end = min(n_samples, test_end + embargo_size)

            train_mask = np.ones(n_samples, dtype=bool)
            train_mask[purge_start:embargo_end] = False

            train_idx = indices[train_mask]
            splits.append((train_idx, test_idx))

        return splits
