"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V14 COMPONENT ABLATION PIPELINE
"""
import unittest
from backtest.research_v14.ablation import run_full_v14_ablation_pipeline


class TestResearchV14Engine(unittest.TestCase):

    def test_v14_pipeline_execution(self):
        res = run_full_v14_ablation_pipeline(days=30, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
