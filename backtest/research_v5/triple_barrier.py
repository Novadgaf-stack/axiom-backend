"""
NEXUS-7 — TRIPLE-BARRIER LABELING ENGINE (RESEARCH V5)
Labels market events using 3 simultaneous barriers: Take-Profit, Stop-Loss, and Max Holding Time.
"""
from typing import Dict, List, Tuple
import numpy as np


class TripleBarrierLabeler:
    """Labels trades by evaluating which barrier is touched first."""

    def __init__(
        self,
        tp_atr_mult: float = 2.0,
        sl_atr_mult: float = 1.0,
        max_hold_bars: int = 48
    ):
        self.tp_atr_mult = tp_atr_mult
        self.sl_atr_mult = sl_atr_mult
        self.max_hold_bars = max_hold_bars

    def label_entry(
        self,
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        atr: np.ndarray,
        entry_idx: int,
        direction: int
    ) -> Dict:
        """
        Returns label (+1 for TP hit first, -1 for SL hit first, 0 for Timeout),
        holding_period, and price_return_pct.
        """
        n = len(prices)
        if entry_idx >= n - 1:
            return {"label": 0, "holding_bars": 0, "return_pct": 0.0, "barrier_hit": "END_OF_DATA"}

        entry_p = prices[entry_idx]
        current_atr = atr[entry_idx] if atr[entry_idx] > 0 else entry_p * 0.01

        if direction == 1: # LONG
            tp_price = entry_p + (self.tp_atr_mult * current_atr)
            sl_price = entry_p - (self.sl_atr_mult * current_atr)
        else: # SHORT
            tp_price = entry_p - (self.tp_atr_mult * current_atr)
            sl_price = entry_p + (self.sl_atr_mult * current_atr)

        end_bar = min(n - 1, entry_idx + self.max_hold_bars)

        for i in range(entry_idx + 1, end_bar + 1):
            curr_high = high[i]
            curr_low = low[i]

            if direction == 1:
                # Conservative: check SL before TP if both touched in same bar
                if curr_low <= sl_price:
                    ret_pct = ((sl_price - entry_p) / entry_p) * 100.0
                    return {"label": -1, "holding_bars": i - entry_idx, "return_pct": ret_pct, "barrier_hit": "STOP_LOSS"}
                if curr_high >= tp_price:
                    ret_pct = ((tp_price - entry_p) / entry_p) * 100.0
                    return {"label": 1, "holding_bars": i - entry_idx, "return_pct": ret_pct, "barrier_hit": "TAKE_PROFIT"}
            else:
                if curr_high >= sl_price:
                    ret_pct = ((entry_p - sl_price) / entry_p) * 100.0
                    return {"label": -1, "holding_bars": i - entry_idx, "return_pct": ret_pct, "barrier_hit": "STOP_LOSS"}
                if curr_low <= tp_price:
                    ret_pct = ((entry_p - tp_price) / entry_p) * 100.0
                    return {"label": 1, "holding_bars": i - entry_idx, "return_pct": ret_pct, "barrier_hit": "TAKE_PROFIT"}

        # Timeout reached
        exit_p = prices[end_bar]
        ret_pct = ((exit_p - entry_p) / entry_p * 100.0) if direction == 1 else ((entry_p - exit_p) / entry_p * 100.0)
        label = 1 if ret_pct > 0 else (-1 if ret_pct < 0 else 0)
        return {"label": label, "holding_bars": end_bar - entry_idx, "return_pct": ret_pct, "barrier_hit": "MAX_HOLD_TIMEOUT"}
