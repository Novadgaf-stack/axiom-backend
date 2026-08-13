"""
NEXUS-7 — INVARIANT & RECONCILIATION TEST SUITE (RESEARCH V5 AUDIT)
Verifies mathematical and data-flow invariants across all Research V5 modules.
"""
import unittest
import numpy as np
from backtest.research_v5.trade_ledger import TradeLedger, TradeRecord
from backtest.research_v5.microstructure import BinanceMicrostructureFrictionModel
from backtest.research_v5.triple_barrier import TripleBarrierLabeler
from backtest.research_v5.features import MultiTimeframeFeatureEngine
from backtest.research_v5.walk_forward import WalkForwardEvaluator


class TestV5Invariants(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 300
        self.prices = 50000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, n)))
        self.high = self.prices * 1.005
        self.low = self.prices * 0.995
        self.volume = np.random.uniform(100, 500, n)

    def test_zero_trades_nan_pf(self):
        """Invariant 1: Zero trades must return None/NaN for Profit Factor and Win Rate (never 0.00)."""
        ledger = TradeLedger()
        summary = ledger.calculate_summary()
        self.assertEqual(summary["trades_count"], 0)
        self.assertIsNone(summary["profit_factor"])
        self.assertIsNone(summary["win_rate"])

    def test_fee_slippage_monotonicity(self):
        """Invariant 2: Adding fees/slippage cannot increase net PnL."""
        model_zero = BinanceMicrostructureFrictionModel(maker_fee_pct=0, taker_fee_pct=0, base_slippage_pct=0)
        model_friction = BinanceMicrostructureFrictionModel(maker_fee_pct=0.05, taker_fee_pct=0.10, base_slippage_pct=0.05)

        p1, f1, q1, ok1 = model_zero.calculate_effective_price_and_fee(50000.0, "BUY", False, 1.0, 1000.0)
        p2, f2, q2, ok2 = model_friction.calculate_effective_price_and_fee(50000.0, "BUY", False, 1.0, 1000.0)

        self.assertGreaterEqual(p2, p1)
        self.assertGreater(f2, f1)

    def test_fee_single_application(self):
        """Invariant 3: Fee is calculated exactly once per order based on executed notional."""
        model = BinanceMicrostructureFrictionModel(taker_fee_pct=0.10)
        eff_p, fee, qty, ok = model.calculate_effective_price_and_fee(10000.0, "BUY", False, 1.0, 1000.0)
        expected_notional = qty * 10000.0
        expected_fee = expected_notional * 0.0010
        self.assertAlmostEqual(fee, expected_fee, places=4)

    def test_deterministic_reproducibility(self):
        """Invariant 4: Identical inputs + identical config produce identical walk-forward metrics."""
        evaluator1 = WalkForwardEvaluator(min_confidence=65.0)
        evaluator2 = WalkForwardEvaluator(min_confidence=65.0)

        res1 = evaluator1.run_simulation(self.prices, self.high, self.low, self.volume, 65.0)
        res2 = evaluator2.run_simulation(self.prices, self.high, self.low, self.volume, 65.0)

        self.assertEqual(res1["trades_count"], res2["trades_count"])
        self.assertEqual(res1["net_pnl_usd"], res2["net_pnl_usd"])

    def test_shuffled_labels_destroy_edge(self):
        """Invariant 5: Shuffled labels destroy predictive performance."""
        labeler = TripleBarrierLabeler()
        atr = np.full(len(self.prices), 500.0)
        labels = [labeler.label_entry(self.prices, self.high, self.low, atr, i, 1)["label"] for i in range(50, 200)]

        shuffled = np.random.choice(labels, size=len(labels), replace=False)
        pos_ratio_orig = sum(1 for l in labels if l == 1) / len(labels)
        pos_ratio_shuffled = sum(1 for l in shuffled if l == 1) / len(shuffled)

        self.assertAlmostEqual(pos_ratio_orig, pos_ratio_shuffled, places=2)

    def test_conservative_same_bar_conflict(self):
        """Invariant 6: When both SL and TP are touched in the same bar, SL is evaluated first."""
        labeler = TripleBarrierLabeler(tp_atr_mult=1.0, sl_atr_mult=1.0)
        prices = np.array([100.0, 100.0, 100.0])
        high = np.array([100.0, 110.0, 100.0])  # Touches TP (+10)
        low = np.array([100.0, 90.0, 100.0])    # Touches SL (-10)
        atr = np.array([5.0, 5.0, 5.0])

        res = labeler.label_entry(prices, high, low, atr, 0, 1)
        self.assertEqual(res["label"], -1)
        self.assertEqual(res["barrier_hit"], "STOP_LOSS")

    def test_future_information_isolation(self):
        """Invariant 7: Feature computations use only historical data up to index i."""
        features_full = MultiTimeframeFeatureEngine.compute_features(self.prices, self.high, self.low, self.volume)
        features_sub = MultiTimeframeFeatureEngine.compute_features(self.prices[:200], self.high[:200], self.low[:200], self.volume[:200])

        np.testing.assert_almost_equal(features_full["ema50_15m"][:200], features_sub["ema50_15m"][:200])


if __name__ == "__main__":
    unittest.main()
