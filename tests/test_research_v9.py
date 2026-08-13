"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V9 DATA QUALITY & LIVE PARITY AUDIT
Verifies ExecutionParityAuditor, LivePortfolioRiskConnector, and V9 audit pipeline execution.
"""
import unittest
from backtest.research_v9.execution_parity import ExecutionParityAuditor
from backtest.research_v9.portfolio_connector import LivePortfolioRiskConnector
from backtest.research_v9.pipeline import run_full_research_v9_pipeline


class TestResearchV9Engine(unittest.TestCase):

    def test_data_realism_classification(self):
        res_vd = ExecutionParityAuditor.classify_data_realism("volume_delta")
        self.assertEqual(res_vd["classification"], "SYNTHETIC_CANDLE_PROXY")

        res_tick = ExecutionParityAuditor.classify_data_realism("websocket_trades")
        self.assertEqual(res_tick["classification"], "TICK_LEVEL_TRUE_ORDER_FLOW")

    def test_engine_parity_auditor(self):
        res = ExecutionParityAuditor.audit_engine_parity(
            backtest_fee_pct=0.05,
            live_maker_fee_pct=0.02,
            live_taker_fee_pct=0.05,
            backtest_slippage_pct=0.03,
            min_notional_usd=10.0,
            qty_step_size=0.001
        )
        self.assertEqual(res["parity_score_pct"], 100.0)
        self.assertEqual(res["verdict"], "PARITY CERTIFIED (100%)")

    def test_live_portfolio_connector(self):
        qty = LivePortfolioRiskConnector.get_volatility_adjusted_quantity(
            equity=10000.0, price=50000.0, atr=500.0, symbol="BTC/USDT", open_positions_count=0
        )
        self.assertGreater(qty, 0.0)

        # Test simultaneous position cap (2)
        qty_cap = LivePortfolioRiskConnector.get_volatility_adjusted_quantity(
            equity=10000.0, price=50000.0, atr=500.0, symbol="BTC/USDT", open_positions_count=2
        )
        self.assertEqual(qty_cap, 0.0)

    def test_v9_pipeline(self):
        res = run_full_research_v9_pipeline("./data/historical", "test_v9_report.md")
        self.assertEqual(res["parity_score_pct"], 100.0)
        self.assertIn("AUDIT PASS", res["verdict"])


if __name__ == "__main__":
    unittest.main()
