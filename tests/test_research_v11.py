"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V11 ORDER BOOK FEATURES & LEAKAGE AUDITOR
Verifies OrderBookFeatureTransformer, DataLeakageAuditor, StrategyEngine integration, and V11 pipeline.
"""
import unittest
from backtest.research_v11.order_book_features import OrderBookFeatureTransformer
from backtest.research_v11.leakage_auditor import DataLeakageAuditor
from backtest.research_v11.pipeline import run_full_research_v11_pipeline
from app.strategy import _summarize_order_book


class TestResearchV11Engine(unittest.TestCase):

    def test_order_book_feature_transformer(self):
        trades = [{"amount": 1.5, "side": "buy"}, {"amount": 0.5, "side": "sell"}]
        depth = {"bid_vol": 10.0, "ask_vol": 5.0, "bids": [[100, 5]], "asks": [[101, 2]]}

        features = OrderBookFeatureTransformer.generate_order_book_features(trades, depth)
        self.assertIn("l2_imbalance", features)
        self.assertIn("tick_cvd_surge", features)
        self.assertEqual(features["classification"], "TICK_LEVEL_TRUE_ORDER_FLOW")

    def test_data_leakage_auditor(self):
        is_set = set(range(0, 7000))
        oos_set = set(range(7000, 10000))
        audit = DataLeakageAuditor.audit_holdout_boundary_isolation(is_set, oos_set)
        self.assertTrue(audit["is_clean"])
        self.assertEqual(audit["leakage_pct"], 0.0)

    def test_strategy_engine_integration(self):
        order_book = {"bids": [[50000, 2.0]], "asks": [[50001, 1.0]]}
        summary = _summarize_order_book(order_book)
        self.assertIn("l2_imbalance", summary)
        self.assertIn("spread_pressure", summary)
        self.assertEqual(summary["classification"], "TICK_LEVEL_TRUE_ORDER_FLOW")

    def test_v11_pipeline(self):
        res = run_full_research_v11_pipeline("./data/historical", "test_v11_report.md")
        self.assertEqual(res["leakage_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
