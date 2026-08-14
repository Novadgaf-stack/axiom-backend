"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V15 COST-AWARE MULTI-TIMEFRAME PIPELINE
"""
import unittest
from backtest.research_v15.cost_aware import run_full_v15_cost_aware_pipeline, resample_candles, generate_synthetic_history


class TestResearchV15Engine(unittest.TestCase):

    def test_resample_candles(self):
        candles_15m = generate_synthetic_history(days=10, timeframe_minutes=15, seed=42)
        candles_30m = resample_candles(candles_15m, factor=2)
        candles_1h = resample_candles(candles_15m, factor=4)
        self.assertEqual(len(candles_30m), len(candles_15m) // 2)
        self.assertEqual(len(candles_1h), len(candles_15m) // 4)

    def test_v15_pipeline_execution(self):
        res = run_full_v15_cost_aware_pipeline(days=30, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
