"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V16 SOL/USDT 1H DEDICATED HYPOTHESIS VALIDATION PIPELINE
"""
import unittest
from backtest.research_v16.sol_validation import run_full_v16_validation_pipeline


class TestResearchV16Engine(unittest.TestCase):

    def test_v16_pipeline_execution(self):
        res = run_full_v16_validation_pipeline(days=30, seed=42)
        self.assertIn("results", res)
        self.assertIn("overall_verdict", res)
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("report_md", res)


if __name__ == "__main__":
    unittest.main()
