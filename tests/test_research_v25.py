"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V25 PROFITABLE HIGH-FREQUENCY EDGE PIPELINE
"""
import unittest
from backtest.research_v25.engine import run_full_v25_pipeline
from backtest.research_v25.frequency_target import calculate_frequency_distribution
from backtest.research_v25.bootstrap_analysis import compute_bootstrap_ci


class TestResearchV25Engine(unittest.TestCase):

    def test_calculate_frequency_distribution(self):
        closed_trades = [
            {"entry_time": "2026-01-01T10:00:00Z"},
            {"entry_time": "2026-01-01T14:00:00Z"},
            {"entry_time": "2026-01-01T18:00:00Z"},
            {"entry_time": "2026-01-02T10:00:00Z"}
        ]
        stats = calculate_frequency_distribution(closed_trades, total_days=10)
        self.assertEqual(stats["avg_trades_per_day"], 0.4)
        self.assertIn("median_trades_per_day", stats)
        self.assertIn("pct_zero_trade_days", stats)

    def test_compute_bootstrap_ci(self):
        pnls = [10.0, -5.0, 15.0, -8.0, 20.0, -4.0, 12.0]
        low, high = compute_bootstrap_ci(pnls, iterations=100)
        self.assertGreater(high, low)

    def test_run_v25_pipeline(self):
        res = run_full_v25_pipeline(days=60, seed=42)
        self.assertIn("overall_verdict", res)
        self.assertIn("results", res)
        self.assertGreaterEqual(len(res["results"]), 3)


if __name__ == "__main__":
    unittest.main()
