"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V23 HIGH-CONFIDENCE EDGE & PAPER TRADING PIPELINE
"""
import unittest
from app.paper_trading_runner import PaperTradingRunner
from backtest.research_v23.high_confidence_edge import run_full_v23_pipeline


class TestResearchV23Engine(unittest.TestCase):

    def test_v23_pipeline_execution(self):
        res = run_full_v23_pipeline(days=60, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertIn("paper_telemetry", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)

    def test_paper_trading_runner_execution(self):
        runner = PaperTradingRunner(initial_equity=10000.0, risk_pct_per_trade=0.005, max_daily_drawdown_pct=0.02)
        order = runner.execute_paper_order("SOL/USDT", "BUY", 145.0, 140.0, 160.0, confidence_score=94, adx=30.0)
        self.assertIsNotNone(order)
        self.assertEqual(order["symbol"], "SOL/USDT")

        closed = runner.close_paper_position(order["order_id"], 155.0, "TAKE_PROFIT")
        self.assertIsNotNone(closed)
        self.assertGreater(closed["net_pnl_usd"], 0)

        telemetry = runner.get_telemetry()
        self.assertEqual(telemetry["total_paper_trades"], 1)
        self.assertEqual(telemetry["win_rate_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
