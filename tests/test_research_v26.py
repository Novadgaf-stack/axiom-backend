"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V26 OPTIMIZED EXPECTANCY PIPELINE
"""
import unittest
import pandas as pd

from backtest.research_v26.strategy_library import (
    MTFTrendPullback,
    BreakoutVolumeExpansion,
    AdaptiveMeanReversion,
    MomentumContinuation,
    DynamicRegimeFilter
)
from backtest.research_v26.data_pipeline import split_chronological_dataset
from backtest.research_v26.statistical_gates import compute_bootstrap_ci, check_statistical_gates, evaluate_trade_sequence
from backtest.research_v26.risk_evaluator import evaluate_risk_sizing_sensitivity
from backtest.research_v26.engine import run_full_v26_pipeline


class TestResearchV26(unittest.TestCase):

    def test_chronological_split(self):
        data = {"timestamp": range(100), "close": range(100), "high": range(100), "low": range(100), "open": range(100), "volume": range(100)}
        df = pd.DataFrame(data)
        tr, val, fw = split_chronological_dataset(df)
        self.assertEqual(len(tr), 50)
        self.assertEqual(len(val), 25)
        self.assertEqual(len(fw), 25)

    def test_bootstrap_ci(self):
        trades = [{"net_pnl": 100.0}, {"net_pnl": 50.0}, {"net_pnl": -30.0}, {"net_pnl": 80.0}, {"net_pnl": -20.0}]
        lower, upper = compute_bootstrap_ci(trades, num_iterations=100)
        self.assertGreater(upper, lower)

    def test_statistical_gates_pass(self):
        metrics = {
            "net_pf": 1.45,
            "bootstrap_ci": (1.12, 1.85),
            "net_expectancy_r": 0.35,
            "max_drawdown_pct": 12.5
        }
        passed, verdict = check_statistical_gates(metrics)
        self.assertTrue(passed)
        self.assertIn("QUALIFIED", verdict)

    def test_statistical_gates_fail(self):
        metrics = {
            "net_pf": 1.10,
            "bootstrap_ci": (0.85, 1.35),
            "net_expectancy_r": 0.05,
            "max_drawdown_pct": 18.0
        }
        passed, verdict = check_statistical_gates(metrics)
        self.assertFalse(passed)
        self.assertIn("REJECTED", verdict)

    def test_risk_evaluator(self):
        trades = [{"r_multiple": 2.0, "net_pnl": 20.0}, {"r_multiple": -1.0, "net_pnl": -10.0}]
        res = evaluate_risk_sizing_sensitivity(trades, total_days=10.0)
        self.assertIn("0.50%", res)
        self.assertIn("0.75%", res)
        self.assertIn("1.00%", res)

    def test_run_v26_pipeline(self):
        res = run_full_v26_pipeline(days=60, seed=42)
        self.assertIn("overall_verdict", res)
        self.assertIn("results", res)
        self.assertTrue(len(res["results"]) > 0)


if __name__ == "__main__":
    unittest.main()
