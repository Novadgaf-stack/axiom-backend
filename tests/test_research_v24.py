"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V24 HIGHER-FREQUENCY EDGE EXPANSION PIPELINE
"""
import unittest
from backtest.research_v24.frequency_expansion import run_full_v24_pipeline


class TestResearchV24Engine(unittest.TestCase):

    def test_v24_pipeline_execution(self):
        res = run_full_v24_pipeline(days=60, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertIn("target_7_verdict", res)
        self.assertIn("best_hf_candidate", res)
        self.assertIn("safe_baseline_candidate", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
