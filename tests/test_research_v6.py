"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V6 STRUCTURAL ALPHA ENGINE
Verifies MTF-TP, LLSR, VEB, EVMR hypothesis signal generators and V6 pipeline execution.
"""
import unittest
import numpy as np
from backtest.research_v5.features import MultiTimeframeFeatureEngine
from backtest.research_v5.microstructure import BinanceMicrostructureFrictionModel
from backtest.research_v6.alpha_hypotheses import StructuralAlphaEngine
from backtest.research_v6.pipeline import run_single_hypothesis_simulation, run_full_research_v6_pipeline


class TestResearchV6Engine(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 300
        self.prices = 50000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, n)))
        self.high = self.prices * 1.005
        self.low = self.prices * 0.995
        self.volume = np.random.uniform(100, 500, n)
        self.features = MultiTimeframeFeatureEngine.compute_features(self.prices, self.high, self.low, self.volume)
        self.friction = BinanceMicrostructureFrictionModel()

    def test_mtf_trend_pullback_hypothesis(self):
        sig = StructuralAlphaEngine.evaluate_mtf_trend_pullback(self.prices, self.high, self.low, self.volume, self.features, 100)
        self.assertIn(sig, [-1, 0, 1])

    def test_liquidity_sweep_hypothesis(self):
        sig = StructuralAlphaEngine.evaluate_liquidity_level_sweep(self.prices, self.high, self.low, self.volume, self.features, 100)
        self.assertIn(sig, [-1, 0, 1])

    def test_volatility_expansion_hypothesis(self):
        sig = StructuralAlphaEngine.evaluate_volatility_expansion_breakout(self.prices, self.high, self.low, self.volume, self.features, 100)
        self.assertIn(sig, [-1, 0, 1])

    def test_extremum_vwap_hypothesis(self):
        sig = StructuralAlphaEngine.evaluate_extremum_vwap_mean_reversion(self.prices, self.high, self.low, self.volume, self.features, 100)
        self.assertIn(sig, [-1, 0, 1])

    def test_single_hypothesis_simulation(self):
        summary = run_single_hypothesis_simulation(
            self.prices, self.high, self.low, self.volume, self.features, self.friction,
            StructuralAlphaEngine.evaluate_mtf_trend_pullback
        )
        self.assertIn("trades_count", summary)
        self.assertIn("net_pnl_usd", summary)

    def test_v6_pipeline(self):
        res = run_full_research_v6_pipeline("./data/historical", "test_v6_report.md")
        self.assertEqual(res["hypotheses_evaluated"], 4)
        self.assertIn("report_path", res)


if __name__ == "__main__":
    unittest.main()
