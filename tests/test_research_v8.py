"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V8 MICROSTRUCTURE & PORTFOLIO ENGINE
Verifies VolumeFlowEngine, MicrostructureAlphaEngine, PortfolioRiskAllocator, and V8 pipeline execution.
"""
import unittest
import numpy as np
from backtest.research_v5.features import MultiTimeframeFeatureEngine
from backtest.research_v5.microstructure import BinanceMicrostructureFrictionModel
from backtest.research_v8.volume_flow import VolumeFlowEngine
from backtest.research_v8.microstructure_alpha import MicrostructureAlphaEngine
from backtest.research_v8.portfolio_allocator import PortfolioRiskAllocator
from backtest.research_v8.pipeline import run_full_research_v8_pipeline


class TestResearchV8Engine(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 300
        self.prices = 50000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, n)))
        self.high = self.prices * 1.005
        self.low = self.prices * 0.995
        self.volume = np.random.uniform(100, 500, n)
        self.features = MultiTimeframeFeatureEngine.compute_features(self.prices, self.high, self.low, self.volume)
        self.flow = VolumeFlowEngine.compute_volume_flow(self.prices, self.high, self.low, self.volume)
        self.friction = BinanceMicrostructureFrictionModel()

    def test_volume_flow_engine(self):
        self.assertIn("vol_delta", self.flow)
        self.assertIn("cvd", self.flow)
        self.assertIn("imbalance_ratio", self.flow)

    def test_volume_delta_absorption(self):
        sig = MicrostructureAlphaEngine.evaluate_volume_delta_absorption(
            self.prices, self.high, self.low, self.volume, self.features, self.flow, 100
        )
        self.assertIn(sig, [-1, 0, 1])

    def test_volume_delta_squeeze(self):
        sig = MicrostructureAlphaEngine.evaluate_volume_delta_squeeze(
            self.prices, self.high, self.low, self.volume, self.features, self.flow, 100
        )
        self.assertIn(sig, [-1, 0, 1])

    def test_pair_spread_reversion(self):
        eth_prices = 3000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, 300)))
        sig_btc, sig_eth = MicrostructureAlphaEngine.evaluate_pair_spread_reversion(self.prices, eth_prices, 100)
        self.assertIn(sig_btc, [-1, 0, 1])
        self.assertIn(sig_eth, [-1, 0, 1])

    def test_portfolio_allocator(self):
        eth_prices = 3000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, 300)))
        corr = PortfolioRiskAllocator.calculate_correlation(self.prices, eth_prices)
        self.assertGreaterEqual(corr, -1.0)
        self.assertLessEqual(corr, 1.0)

        qty = PortfolioRiskAllocator.calculate_volatility_target_size(10000.0, 50000.0, 500.0)
        self.assertGreater(qty, 0.0)

    def test_v8_pipeline(self):
        res = run_full_research_v8_pipeline("./data/historical", "test_v8_report.md")
        self.assertIn("verdict", res)


if __name__ == "__main__":
    unittest.main()
