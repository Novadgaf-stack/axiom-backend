"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V7 MTF-TP ROBUSTNESS EVALUATOR
Verifies MTFTPRobustnessEvaluator parameter neighborhood, cost stress matrix, and V7 pipeline execution.
"""
import unittest
import numpy as np
from backtest.research_v5.features import MultiTimeframeFeatureEngine
from backtest.research_v5.microstructure import BinanceMicrostructureFrictionModel
from backtest.research_v7.robustness_evaluator import MTFTPRobustnessEvaluator
from backtest.research_v7.pipeline import run_full_research_v7_pipeline


class TestResearchV7Engine(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 500
        self.prices = 50000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, n)))
        self.high = self.prices * 1.005
        self.low = self.prices * 0.995
        self.volume = np.random.uniform(100, 500, n)
        self.features = MultiTimeframeFeatureEngine.compute_features(self.prices, self.high, self.low, self.volume)
        self.friction = BinanceMicrostructureFrictionModel()

    def test_custom_simulation(self):
        summary = MTFTPRobustnessEvaluator.run_simulation_custom(
            self.prices, self.high, self.low, self.volume, self.features, self.friction
        )
        self.assertIn("trades_count", summary)
        self.assertIn("net_pnl_usd", summary)

    def test_directional_attribution(self):
        long_summary = MTFTPRobustnessEvaluator.run_simulation_custom(
            self.prices, self.high, self.low, self.volume, self.features, self.friction, direction_filter="LONG_ONLY"
        )
        short_summary = MTFTPRobustnessEvaluator.run_simulation_custom(
            self.prices, self.high, self.low, self.volume, self.features, self.friction, direction_filter="SHORT_ONLY"
        )
        self.assertIn("trades_count", long_summary)
        self.assertIn("trades_count", short_summary)

    def test_parameter_grid(self):
        grid = MTFTPRobustnessEvaluator.evaluate_parameter_grid(
            self.prices, self.high, self.low, self.volume, self.features, self.friction
        )
        self.assertEqual(len(grid), 27)

    def test_cost_stress_matrix(self):
        stress = MTFTPRobustnessEvaluator.evaluate_cost_stress(
            self.prices, self.high, self.low, self.volume, self.features
        )
        self.assertIn("Tier 1 (Low Cost)", stress)
        self.assertIn("Tier 3 (Severe Stress)", stress)

    def test_v7_pipeline(self):
        res = run_full_research_v7_pipeline("./data/historical", "test_v7_report.md")
        self.assertIn("verdict", res)
        self.assertIn("grid_stability_pct", res)


if __name__ == "__main__":
    unittest.main()
