"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V18 ROBUSTNESS & EDGE DISCOVERY PIPELINE
"""
import unittest
from backtest.research_v18.robustness_edge import run_full_v18_pipeline


class TestResearchV18Engine(unittest.TestCase):

    def test_v18_pipeline_execution(self):
        res = run_full_v18_pipeline(days=30, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
