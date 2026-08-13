"""
NEXUS-7 — HARD PORTFOLIO DRAWDOWN CIRCUIT BREAKER (RESEARCH V10)
Enforces a hard 15.0% peak-to-trough portfolio drawdown circuit breaker.
"""
from app.logging_setup import get_logger

logger = get_logger("risk")


class PortfolioDrawdownGuard:
    """Enforces a maximum 15.0% peak-to-trough portfolio drawdown circuit breaker."""

    def __init__(self, max_portfolio_dd_pct: float = 15.0):
        self.max_portfolio_dd_pct = max_portfolio_dd_pct
        self._peak_equity: float = 0.0

    def update_peak(self, current_equity: float):
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity

    def calculate_drawdown(self, current_equity: float) -> float:
        if self._peak_equity <= 0:
            return 0.0
        if current_equity >= self._peak_equity:
            return 0.0
        return ((self._peak_equity - current_equity) / self._peak_equity) * 100.0

    def is_circuit_breaker_triggered(self, current_equity: float) -> bool:
        self.update_peak(current_equity)
        dd_pct = self.calculate_drawdown(current_equity)
        if dd_pct >= self.max_portfolio_dd_pct:
            logger.warning(
                f"Portfolio Circuit Breaker Triggered: Peak-to-Trough Drawdown {dd_pct:.2f}% "
                f">= Hard Limit {self.max_portfolio_dd_pct}%. New trades BLOCKED."
            )
            return True
        return False
