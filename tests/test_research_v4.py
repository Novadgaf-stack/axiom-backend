"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V4 ENGINE
Verifies MarketRegime, StrategyEnsemble, Consensus, WalkForward, PBO, and ExperimentRegistry.
"""
import unittest
import numpy as np
import os
import tempfile
from backtest.research_v4.regime import RegimeDetector, MarketRegime
from backtest.research_v4.strategies import TrendFollowingStrategy, MeanReversionStrategy
from backtest.research_v4.consensus import StrategyConsensusEngine
from backtest.research_v4.walk_forward import WalkForwardEvaluator
from backtest.research_v4.pbo import OverfittingAuditor
from backtest.research_v4.registry import ExperimentRegistry


class TestResearchV4Engine(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 300
        self.prices = 50000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, n)))
        self.high = self.prices * 1.005
        self.low = self.prices * 0.995
        self.volume = np.random.uniform(100, 500, n)

    def test_regime_detector(self):
        indicators = RegimeDetector.calculate_indicators(self.prices, self.high, self.low)
        self.assertIn("ema50", indicators)
        self.assertIn("ema200", indicators)
        self.assertIn("atr_ratio", indicators)

        regime = RegimeDetector.detect_regime(
            self.prices[-1],
            indicators["ema50"][-1],
            indicators["ema200"][-1],
            indicators["atr_ratio"][-1],
            indicators["adx"][-1]
        )
        self.assertIsInstance(regime, MarketRegime)

    def test_strategy_consensus(self):
        engine = StrategyConsensusEngine()
        res = engine.evaluate_consensus(
            self.prices, self.high, self.low, self.volume, MarketRegime.TRENDING_BULL, 100
        )
        self.assertIn("signal", res)
        self.assertIn("confidence", res)
        self.assertIn("votes", res)

    def test_walk_forward_evaluator(self):
        evaluator = WalkForwardEvaluator(fee_pct=0.1, slippage_pct=0.05)
        res = evaluator.evaluate_walk_forward_and_holdout(
            self.prices, self.high, self.low, self.volume, n_windows=2
        )
        self.assertIn("walk_forward_windows", res)
        self.assertIn("untouched_oos_holdout", res)
        self.assertEqual(len(res["walk_forward_windows"]), 2)

    def test_overfitting_auditor(self):
        bh = OverfittingAuditor.calculate_buy_and_hold(self.prices)
        self.assertIn("bh_net_pnl", bh)

        wf_dummy = {
            "walk_forward_windows": [
                {"net_pnl": 100.0},
                {"net_pnl": -50.0},
            ]
        }
        pbo = OverfittingAuditor.evaluate_pbo(wf_dummy, n_resamples=50)
        self.assertIn("pbo_pct", pbo)
        self.assertIn("verdict", pbo)

    def test_experiment_registry(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            reg = ExperimentRegistry(registry_path=tmp_path)
            h = reg.log_experiment("test_exp", "test_hyp", {"param": 1}, {"pnl": 10.0})
            self.assertTrue(reg.is_experiment_logged(h))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
