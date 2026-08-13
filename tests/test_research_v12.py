"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V12 DRAWDOWN AUTO-RECOVERY & FEATURE TIMING AUDIT
Verifies PortfolioDrawdownGuard auto-recovery & daily reset, FeatureTimingAuditor, and V12 pipeline execution.
"""
import unittest
from backtest.research_v10.drawdown_guard import PortfolioDrawdownGuard
from backtest.research_v12.feature_timing import FeatureTimingAuditor
from backtest.research_v12.pipeline import run_full_research_v12_pipeline
from app.risk import RiskManager


class TestResearchV12Engine(unittest.TestCase):

    def test_drawdown_guard_auto_recovery(self):
        guard = PortfolioDrawdownGuard(max_portfolio_dd_pct=15.0, recovery_buffer_pct=5.0, initial_equity=10000.0)
        guard.update_peak(10000.0)

        # Trigger circuit breaker (20% DD >= 15%)
        self.assertTrue(guard.is_circuit_breaker_triggered(8000.0))

        # Still blocked at 8,500 (15% DD > 5% recovery buffer)
        self.assertTrue(guard.is_circuit_breaker_triggered(8500.0))

        # Auto-recovery unlocked at 9,600 (4% DD <= 5% recovery buffer)
        self.assertFalse(guard.is_circuit_breaker_triggered(9600.0))

    def test_drawdown_guard_daily_reset(self):
        guard = PortfolioDrawdownGuard(max_portfolio_dd_pct=15.0, recovery_buffer_pct=5.0, initial_equity=10000.0)
        guard.is_circuit_breaker_triggered(8000.0)
        self.assertTrue(guard._circuit_breaker_active)

        # Daily reset on UTC day rollover
        guard.reset_daily_peak(8000.0)
        self.assertFalse(guard._circuit_breaker_active)
        self.assertEqual(guard._peak_equity, 8000.0)

    def test_risk_manager_daily_reset(self):
        rm = RiskManager()
        rm.drawdown_guard.is_circuit_breaker_triggered(8000.0)
        rm._roll_day_if_needed(8000.0)
        self.assertFalse(rm.drawdown_guard._circuit_breaker_active)

    def test_feature_timing_auditor(self):
        res = FeatureTimingAuditor.audit_timestamp_parity(
            candle_timestamp_ms=1000, tick_timestamp_ms=500, feature_calculation_time_ms=1002
        )
        self.assertEqual(res["parity_score_pct"], 100.0)
        self.assertFalse(res["has_lookahead"])

    def test_v12_pipeline(self):
        res = run_full_research_v12_pipeline("./data/historical", "test_v12_report.md")
        self.assertTrue(res["auto_recovery_verified"])


if __name__ == "__main__":
    unittest.main()
