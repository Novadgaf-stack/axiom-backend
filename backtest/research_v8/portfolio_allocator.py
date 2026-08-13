"""
NEXUS-7 — PORTFOLIO RISK & VOLATILITY ALLOCATOR (RESEARCH V8)
Manages cross-asset correlation, inverse volatility sizing, and simultaneous position caps.
"""
from typing import Dict, Tuple
import numpy as np


class PortfolioRiskAllocator:
    """Manages joint BTC/ETH portfolio risk allocation and volatility targeting."""

    @staticmethod
    def calculate_correlation(prices1: np.ndarray, prices2: np.ndarray) -> float:
        if len(prices1) < 10 or len(prices2) < 10:
            return 1.0
        min_len = min(len(prices1), len(prices2))
        corr_matrix = np.corrcoef(prices1[-min_len:], prices2[-min_len:])
        return float(corr_matrix[0, 1])

    @staticmethod
    def calculate_volatility_target_size(
        equity: float,
        price: float,
        atr: float,
        target_risk_pct: float = 0.01  # 1% equity risk target per trade
    ) -> float:
        if atr <= 0 or price <= 0:
            return 0.0

        risk_usd = equity * target_risk_pct
        qty = risk_usd / (2.0 * atr)  # Risk 2.0x ATR
        notional = qty * price

        # Max allocation cap (25% equity per position)
        max_notional = equity * 0.25
        if notional > max_notional:
            qty = max_notional / price

        return qty
