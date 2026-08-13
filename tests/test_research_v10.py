"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V10 REAL DATA & DRAWDOWN GUARD ENGINE
Verifies RealDataIngestionEngine, PortfolioDrawdownGuard, and V10 pipeline execution.
"""
import unittest
from backtest.research_v10.data_ingestion import RealDataIngestionEngine
from backtest.research_v10.drawdown_guard import PortfolioDrawdownGuard
from backtest.research_v10.pipeline import run_full_research_v10_pipeline
from app.risk import RiskManager


class TestResearchV10Engine(unittest.TestCase):

    def test_real_data_ingestion(self):
        ticks = RealDataIngestionEngine.ingest_public_trade_ticks(symbol="BTC/USDT", limit=100)
        self.assertEqual(len(ticks), 100)
        self.assertIn("price", ticks[0])
        self.assertIn("side", ticks[0])

        depth = RealDataIngestionEngine.ingest_l2_order_book_depth(symbol="BTC/USDT")
        self.assertIn("bids", depth)
        self.assertIn("asks", depth)
        self.assertEqual(depth["classification"], "TICK_LEVEL_TRUE_ORDER_FLOW")

        delta = RealDataIngestionEngine.compute_true_order_flow_delta(ticks)
        self.assertIn("vol_delta", delta)
        self.assertEqual(delta["classification"], "TICK_LEVEL_TRUE_ORDER_FLOW")

    def test_drawdown_guard(self):
        guard = PortfolioDrawdownGuard(max_portfolio_dd_pct=15.0)
        guard.update_peak(10000.0)
        self.assertFalse(guard.is_circuit_breaker_triggered(9000.0))  # 10% DD < 15%
        self.assertTrue(guard.is_circuit_breaker_triggered(8000.0))   # 20% DD >= 15%

    def test_risk_manager_integration(self):
        rm = RiskManager()
        rm.drawdown_guard.update_peak(10000.0)
        self.assertTrue(rm.check_portfolio_drawdown(8000.0))

    def test_v10_pipeline(self):
        res = run_full_research_v10_pipeline("./data/historical", "test_v10_report.md")
        self.assertLessEqual(res["max_drawdown_pct"], 15.0)


if __name__ == "__main__":
    unittest.main()
