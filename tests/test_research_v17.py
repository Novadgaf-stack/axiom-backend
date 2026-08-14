"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V17 REGIME FILTER & DYNAMIC EXIT PIPELINE
"""
import unittest
from backtest.research_v17.regime_exit import run_full_v17_pipeline


class TestResearchV17Engine(unittest.TestCase):

    def test_v17_pipeline_execution(self):
        res = run_full_v17_pipeline(days=30, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
