"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V13 STRATEGY OPTIMIZER & OUT-OF-SAMPLE PIPELINE
"""
import unittest
from backtest.research_v13.optimizer import run_full_v13_research_pipeline, partition_candles, generate_synthetic_history


class TestResearchV13Engine(unittest.TestCase):

    def test_partition_candles(self):
        candles = generate_synthetic_history(days=10, timeframe_minutes=15, seed=42)
        is_c, oos_c = partition_candles(candles, is_ratio=0.7)
        self.assertEqual(len(is_c) + len(oos_c), len(candles))
        self.assertAlmostEqual(len(is_c) / len(candles), 0.7, delta=0.01)

    def test_v13_pipeline_execution(self):
        res = run_full_v13_research_pipeline(days=30, seed=42)
        self.assertIn("metrics", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["metrics"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
