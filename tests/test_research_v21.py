"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V21 TRADE SELECTION & EXIT EFFICIENCY EDGE EXPANSION PIPELINE
"""
import unittest
from backtest.research_v21.edge_expansion import run_full_v21_pipeline


class TestResearchV21Engine(unittest.TestCase):

    def test_v21_pipeline_execution(self):
        res = run_full_v21_pipeline(days=60, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
