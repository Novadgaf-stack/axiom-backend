"""
NEXUS-7 — BINANCE MICROSTRUCTURE FRICTION MODEL (RESEARCH V5)
Realistic exchange friction modeling including maker/taker fees, spread,
volatility-dependent slippage, minimum notional ($10), and lot size step-size.
"""
import math
from typing import Dict, Tuple


class BinanceMicrostructureFrictionModel:
    """Models realistic Binance Spot / Futures market microstructure friction."""

    def __init__(
        self,
        maker_fee_pct: float = 0.02,
        taker_fee_pct: float = 0.05,
        half_spread_pct: float = 0.01,
        base_slippage_pct: float = 0.03,
        min_notional_usd: float = 10.0,
        qty_step_size: float = 0.001,
    ):
        self.maker_fee = maker_fee_pct / 100.0
        self.taker_fee = taker_fee_pct / 100.0
        self.half_spread = half_spread_pct / 100.0
        self.base_slippage = base_slippage_pct / 100.0
        self.min_notional_usd = min_notional_usd
        self.qty_step_size = qty_step_size

    def calculate_effective_price_and_fee(
        self,
        raw_price: float,
        side: str,
        is_maker: bool,
        atr_ratio: float,
        equity_allocated: float
    ) -> Tuple[float, float, float, bool]:
        """
        Calculates (effective_execution_price, total_fee_usd, rounded_quantity, is_valid).
        """
        # Step-size quantity calculation & min notional check
        raw_qty = equity_allocated / raw_price
        rounded_qty = math.floor(raw_qty / self.qty_step_size) * self.qty_step_size
        notional_usd = rounded_qty * raw_price

        if notional_usd < self.min_notional_usd or rounded_qty <= 0:
            return raw_price, 0.0, 0.0, False

        # Dynamic slippage scaling with volatility expansion
        vol_multiplier = math.sqrt(max(1.0, atr_ratio))
        dynamic_slippage = self.base_slippage * vol_multiplier

        # Spread & slippage adjustment
        direction = 1.0 if side.upper() in ("BUY", "LONG") else -1.0
        friction_pct = self.half_spread + dynamic_slippage
        effective_price = raw_price * (1.0 + (direction * friction_pct))

        # Fee calculation
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        total_fee_usd = notional_usd * fee_rate

        return effective_price, total_fee_usd, rounded_qty, True
