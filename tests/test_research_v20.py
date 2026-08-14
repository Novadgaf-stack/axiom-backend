"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V20 REGIME-AWARE RISK-CONTROLLED EDGE OPTIMIZATION PIPELINE
"""
import unittest
from backtest.research_v20.regime_risk_optimization import run_full_v20_pipeline


class TestResearchV20Engine(unittest.TestCase):

    def test_v20_pipeline_execution(self):
        res = run_full_v20_pipeline(days=60, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
