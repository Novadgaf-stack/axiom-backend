"""
NEXUS-7 — PORTFOLIO RISK CONNECTOR (RESEARCH V9)
Connects PortfolioRiskAllocator inverse volatility targeting to RiskManagerPro.
"""
from typing import Optional
from backtest.research_v8.portfolio_allocator import PortfolioRiskAllocator
from app.logging_setup import get_logger

logger = get_logger("risk")


class LivePortfolioRiskConnector:
    """Bridges Research V8 Portfolio Allocator with Live RiskManager."""

    @staticmethod
    def get_volatility_adjusted_quantity(
        equity: float,
        price: float,
        atr: float,
        symbol: str,
        open_positions_count: int
    ) -> float:
        """Calculates volatility-targeted position quantity with joint portfolio caps."""
        if open_positions_count >= 2:
            logger.info(f"[{symbol}] Rejected by Portfolio Connector: Simultaneous position limit reached (2).")
            return 0.0

        qty = PortfolioRiskAllocator.calculate_volatility_target_size(
            equity=equity,
            price=price,
            atr=atr,
            target_risk_pct=0.01  # 1% equity risk cap
        )
        return qty
