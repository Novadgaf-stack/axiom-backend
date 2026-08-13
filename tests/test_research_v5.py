"""
NEXUS-7 — UNIT TESTS FOR RESEARCH V5 FRAMEWORK
Verifies MultiTimeframeFeatures, BinanceMicrostructure, TripleBarrier, PurgedCV, Ablation, DeflatedSharpe, and PromotionGate.
"""
import unittest
import numpy as np
from backtest.research_v5.features import MultiTimeframeFeatureEngine
from backtest.research_v5.microstructure import BinanceMicrostructureFrictionModel
from backtest.research_v5.triple_barrier import TripleBarrierLabeler
from backtest.research_v5.purged_cv import PurgedCrossValidator
from backtest.research_v5.ablation import AblationAuditor
from backtest.research_v5.deflated_sharpe import DeflatedSharpeAuditor
from backtest.research_v5.promotion_gate import HardPromotionGate


class TestResearchV5Framework(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 300
        self.prices = 50000.0 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, n)))
        self.high = self.prices * 1.005
        self.low = self.prices * 0.995
        self.volume = np.random.uniform(100, 500, n)

    def test_mtf_features(self):
        feats = MultiTimeframeFeatureEngine.compute_features(self.prices, self.high, self.low, self.volume)
        self.assertIn("ema50_15m", feats)
        self.assertIn("bias_4h", feats)
        self.assertIn("volume_imbalance", feats)

    def test_microstructure_model(self):
        model = BinanceMicrostructureFrictionModel()
        eff_price, fee_usd, qty, ok = model.calculate_effective_price_and_fee(
            50000.0, "BUY", is_maker=False, atr_ratio=1.2, equity_allocated=1000.0
        )
        self.assertTrue(ok)
        self.assertGreater(eff_price, 50000.0)
        self.assertGreater(fee_usd, 0.0)

    def test_triple_barrier_labeler(self):
        labeler = TripleBarrierLabeler(tp_atr_mult=2.0, sl_atr_mult=1.0, max_hold_bars=48)
        atr = np.full(len(self.prices), 500.0)
        lbl = labeler.label_entry(self.prices, self.high, self.low, atr, 50, 1)
        self.assertIn("label", lbl)
        self.assertIn("barrier_hit", lbl)

    def test_purged_cross_validator(self):
        cv = PurgedCrossValidator(n_splits=3, pct_embargo=0.02, max_hold_bars=20)
        splits = cv.split(len(self.prices))
        self.assertEqual(len(splits), 3)

    def test_ablation_auditor(self):
        feats = MultiTimeframeFeatureEngine.compute_features(self.prices, self.high, self.low, self.volume)
        friction = BinanceMicrostructureFrictionModel()
        res = AblationAuditor.run_ablation_study(self.prices, self.high, self.low, self.volume, feats, friction)
        self.assertEqual(len(res), 5)
        self.assertIn("step_name", res[0])


    def test_deflated_sharpe(self):
        dsr = DeflatedSharpeAuditor.calculate_dsr(observed_sharpe=-0.5, num_trials=20)
        self.assertIn("dsr_prob", dsr)
        self.assertIn("verdict", dsr)

    def test_promotion_gate(self):
        controls = HardPromotionGate.evaluate_baseline_controls(self.prices)
        self.assertIn("Buy_and_Hold", controls)

        gate = HardPromotionGate.evaluate_7stage_gate(
            is_pf=0.0, is_win_rate=0.0, wf_profitable_pct=0.0,
            oos_pnl=0.0, oos_pf=0.0, pbo_pct=80.0, dsr_prob=0.0, stress_expectancy=-10.0
        )
        self.assertEqual(gate["final_verdict"], "REJECTED (NO EDGE PROVEN)")


if __name__ == "__main__":
    unittest.main()
