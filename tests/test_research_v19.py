"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V19 FROZEN PARAMETER LONG-HORIZON FORWARD VALIDATION PIPELINE
"""
import unittest
from backtest.research_v19.long_horizon_validation import run_full_v19_pipeline


class TestResearchV19Engine(unittest.TestCase):

    def test_v19_pipeline_execution(self):
        res = run_full_v19_pipeline(days=60, seed=42)
        self.assertIn("overall_results", res)
        self.assertIn("quarterly_results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["overall_results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
