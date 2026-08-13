"""
Automated Test Suite for Nexus-7 Solana Agent Layer.
"""
import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from solana_agent.config import solana_settings, SolanaSettings
from solana_agent.policy_gate import SolanaPolicyGate


class TestSolanaAgent(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = settings.ENGINE_TOKEN or settings.api_auth_token or "test_token"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_policy_gate_pass(self):
        gate = SolanaPolicyGate()
        res = gate.evaluate_policy(sol_amount=0.05, confidence_score=88.0)
        self.assertTrue(res.passed)
        self.assertIsNone(res.rejection_reason)

    def test_policy_gate_reject_oversized(self):
        gate = SolanaPolicyGate()
        res = gate.evaluate_policy(sol_amount=1.5, confidence_score=88.0)
        self.assertFalse(res.passed)
        self.assertFalse(res.sol_cap_valid)
        self.assertIn("exceeds max_sol_per_tx", res.rejection_reason)

    def test_policy_gate_confidence_floor(self):
        gate = SolanaPolicyGate()
        res = gate.evaluate_policy(sol_amount=0.05, confidence_score=70.0)
        self.assertFalse(res.passed)
        self.assertFalse(res.confidence_valid)
        self.assertIn("below floor", res.rejection_reason)

    def test_policy_gate_rate_limit(self):
        gate = SolanaPolicyGate()
        for _ in range(5):
            gate.record_execution()
        res = gate.evaluate_policy(sol_amount=0.05, confidence_score=88.0)
        self.assertFalse(res.passed)
        self.assertFalse(res.rate_limit_valid)
        self.assertIn("hourly_rate_limit_exceeded", res.rejection_reason)

    def test_cluster_lock_rejection(self):
        bad_settings = SolanaSettings(
            solana_rpc_url="https://api.mainnet-beta.solana.com",
            solana_cluster="mainnet"
        )
        problems = bad_settings.validate()
        self.assertTrue(len(problems) > 0)
        self.assertIn("Mainnet Solana cluster requested", problems[0])

    def test_solana_status_endpoint(self):
        res = self.client.get("/api/solana/status", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("cluster"), "devnet")
        self.assertIn("wallet_public_key", data)

    def test_solana_evaluate_endpoint_pass(self):
        payload = {
            "symbol": "SOL/USDT",
            "action": "EXECUTE_DEVNET_SWAP",
            "sol_amount": 0.05,
            "confidence_score": 88.0,
            "reasoning": "Bullish trend confirmed"
        }
        res = self.client.post("/api/solana/evaluate", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["policy_check"]["passed"])
        self.assertTrue(data["simulation"]["success"])
        self.assertEqual(data["execution"]["status"], "EXECUTED")
        self.assertIsNotNone(data["execution"]["tx_signature"])

    def test_solana_evaluate_endpoint_reject(self):
        payload = {
            "symbol": "SOL/USDT",
            "action": "EXECUTE_DEVNET_SWAP",
            "sol_amount": 2.5,  # Exceeds max 0.1 SOL cap
            "confidence_score": 88.0,
            "reasoning": "Oversized test"
        }
        res = self.client.post("/api/solana/evaluate", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["policy_check"]["passed"])
        self.assertEqual(data["action"], "HOLD")
        self.assertEqual(data["execution"]["status"], "REJECTED")

    def test_solana_history_endpoint(self):
        res = self.client.get("/api/solana/history", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)


if __name__ == "__main__":
    unittest.main()
