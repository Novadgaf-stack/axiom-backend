import unittest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.config import settings
from app.state import state, EngineStatus


class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = settings.ENGINE_TOKEN or settings.api_auth_token or "test_token"

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})

    def test_auth_failure(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 401)

    def test_auth_bearer(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.get("/api/status", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertIn("equity", data)
        self.assertIn("balance", data)
        self.assertIn("last_equity_usd", data)

    def test_auth_custom_header(self):
        headers = {"x-api-key": self.token}
        res = self.client.get("/api/status", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("balance", data)

    def test_auth_query_param(self):
        res = self.client.get(f"/api/status?token={self.token}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("balance", data)

    def test_balance_endpoints(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        for ep in ["/api/balance", "/api/account/balance", "/api/account"]:
            res = self.client.get(ep, headers=headers)
            self.assertEqual(res.status_code, 200, f"Failed on endpoint {ep}")
            data = res.json()
            self.assertIn("equity", data)
            self.assertIn("balance", data)
            self.assertIn("usdt_balance", data)
            self.assertIn("total_balance", data)
            self.assertIn("available_balance", data)
            self.assertIn("daily_pnl_usd", data)
            self.assertIn("total_pnl_usd", data)

    def test_positions_trades_decisions(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        for ep in ["/api/positions", "/api/trades", "/api/decisions", "/api/equity-curve"]:
            res = self.client.get(ep, headers=headers)
            self.assertEqual(res.status_code, 200, f"Failed on endpoint {ep}")


if __name__ == "__main__":
    unittest.main()
