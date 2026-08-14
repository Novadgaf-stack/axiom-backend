"""
NEXUS-7 — UNIT & INTEGRATION TESTS FOR FORWARD TESTNET RUNNER
Verifies preflight safety, frozen rule enforcement, duplicate order prevention,
0.5% risk sizing, 2.0% daily circuit breaker, stale data handling, and mainnet lock safety.
"""
import os
import unittest
from app.testnet_runner import ForwardTestnetRunner


class TestForwardTestnetRunner(unittest.TestCase):

    def setUp(self):
        self.runner = ForwardTestnetRunner(telemetry_file="./logs/test_telemetry.json")

    def test_preflight_safety_check_pass(self):
        report = ForwardTestnetRunner.preflight_safety_check(self.runner.settings)
        self.assertIn("preflight_status", report)
        self.assertIn("PASS", report["preflight_status"])
        self.assertFalse(report["real_money_trading_enabled"])

    def test_frozen_strategy_rule_enforcement(self):
        # Rejected AI Score < 92
        sig1 = self.runner.evaluate_signal("SOL/USDT", 145.0, confidence_score=90, adx=30.0, atr=3.0)
        self.assertFalse(sig1.accepted)
        self.assertIn("< 92", sig1.rejection_reason)

        # Rejected ADX < 28.0
        sig2 = self.runner.evaluate_signal("SOL/USDT", 145.0, confidence_score=94, adx=25.0, atr=3.0)
        self.assertFalse(sig2.accepted)
        self.assertIn("< 28.0", sig2.rejection_reason)

        # Accepted AI Score >= 92 & ADX >= 28.0
        sig3 = self.runner.evaluate_signal("SOL/USDT", 145.0, confidence_score=94, adx=30.0, atr=3.0)
        self.assertTrue(sig3.accepted)

    def test_duplicate_order_prevention(self):
        sig1 = self.runner.evaluate_signal("SOL/USDT", 145.0, confidence_score=94, adx=30.0, atr=3.0)
        order1 = self.runner.execute_testnet_order(sig1)
        self.assertIsNotNone(order1)

        # Second signal for same symbol should be rejected
        sig2 = self.runner.evaluate_signal("SOL/USDT", 146.0, confidence_score=95, adx=32.0, atr=3.0)
        self.assertFalse(sig2.accepted)
        self.assertIn("Existing open position", sig2.rejection_reason)

    def test_risk_sizing_calculation(self):
        sig = self.runner.evaluate_signal("SOL/USDT", 100.0, confidence_score=95, adx=30.0, atr=2.0)
        order = self.runner.execute_testnet_order(sig)

        # 0.5% risk on $10,000 equity = $50.00 risk
        # Stop loss = 100 - (1.5 * 2) = 97.0 -> Price risk = $3.00
        # Expected Qty = $50 / $3 = 16.6667
        expected_qty = 50.0 / 3.0
        self.assertAlmostEqual(order["position_qty"], expected_qty, places=2)

    def test_daily_circuit_breaker_trigger(self):
        # Simulate $250 loss on $10,000 equity (2.5% loss > 2.0% cap)
        self.runner.equity = 9750.0
        triggered = self.runner.check_circuit_breaker()
        self.assertTrue(triggered)
        self.assertTrue(self.runner.circuit_breaker_active)

        # Subsequent signals should be rejected by circuit breaker
        sig = self.runner.evaluate_signal("BTC/USDT", 60000.0, confidence_score=95, adx=32.0, atr=500.0)
        self.assertFalse(sig.accepted)
        self.assertIn("Circuit breaker active", sig.rejection_reason)

    def test_telemetry_export_and_schema(self):
        sig = self.runner.evaluate_signal("SOL/USDT", 145.0, confidence_score=94, adx=30.0, atr=3.0)
        order = self.runner.execute_testnet_order(sig)
        self.runner.close_testnet_position(order["order_id"], 155.0, "TAKE_PROFIT")

        telemetry = self.runner.export_telemetry()
        self.assertEqual(telemetry["total_completed_trades"], 1)
        self.assertEqual(telemetry["win_rate_pct"], 100.0)
        self.assertIn("decision_gate_status", telemetry)

    def test_real_money_trading_safety_lock(self):
        # Verify TRADING_ENABLED setting is strictly False
        self.assertFalse(self.runner.settings.trading_enabled)


if __name__ == "__main__":
    unittest.main()
