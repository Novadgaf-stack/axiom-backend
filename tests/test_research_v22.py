"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V22 TRADE-LEVEL EDGE ATTRIBUTION PIPELINE
"""
import unittest
from backtest.research_v22.trade_attribution import run_full_v22_pipeline


class TestResearchV22Engine(unittest.TestCase):

    def test_v22_pipeline_execution(self):
        res = run_full_v22_pipeline(days=60, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
