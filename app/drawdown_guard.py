"""
NEXUS-7 — PORTFOLIO DRAWDOWN CIRCUIT BREAKER (APP MODULE)
Self-contained risk guard module for live execution engine.
"""
from app.logging_setup import get_logger

logger = get_logger("risk")


class PortfolioDrawdownGuard:
    """Enforces max 15.0% portfolio drawdown circuit breaker with auto-recovery."""

    def __init__(
        self,
        max_portfolio_dd_pct: float = 15.0,
        recovery_buffer_pct: float = 5.0,
        initial_equity: float = 10000.0
    ):
        self.max_portfolio_dd_pct = max_portfolio_dd_pct
        self.recovery_buffer_pct = recovery_buffer_pct
        self._peak_equity: float = initial_equity
        self._circuit_breaker_active: bool = False

    def update_peak(self, current_equity: float):
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity
            if self._circuit_breaker_active:
                self._circuit_breaker_active = False
                logger.info(f"Portfolio Circuit Breaker UNLOCKED: New peak equity achieved ${current_equity:,.2f}.")

    def reset_daily_peak(self, current_equity: float):
        """Resets peak equity on UTC day roll to prevent multi-day permanent lockout."""
        self._peak_equity = current_equity
        self._circuit_breaker_active = False
        logger.info(f"Portfolio Circuit Breaker daily reset. Peak equity reset to ${current_equity:,.2f}.")

    def calculate_drawdown(self, current_equity: float) -> float:
        if self._peak_equity <= 0:
            return 0.0
        if current_equity >= self._peak_equity:
            return 0.0
        return ((self._peak_equity - current_equity) / self._peak_equity) * 100.0

    def is_circuit_breaker_triggered(self, current_equity: float) -> bool:
        self.update_peak(current_equity)
        dd_pct = self.calculate_drawdown(current_equity)

        if self._circuit_breaker_active:
            if dd_pct <= self.recovery_buffer_pct:
                self._circuit_breaker_active = False
                logger.info(
                    f"Portfolio Circuit Breaker UNLOCKED (Auto-Recovery): Equity recovered to "
                    f"${current_equity:,.2f} (Drawdown {dd_pct:.2f}% <= Recovery Buffer {self.recovery_buffer_pct}%)."
                )
                return False
            return True

        if dd_pct >= self.max_portfolio_dd_pct:
            self._circuit_breaker_active = True
            logger.warning(
                f"Portfolio Circuit Breaker TRIGGERED: Peak-to-Trough Drawdown {dd_pct:.2f}% "
                f">= Hard Limit {self.max_portfolio_dd_pct}%. New trades BLOCKED."
            )
            return True

        return False
