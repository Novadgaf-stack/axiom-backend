"""
Unit tests for AI decision parsing, confidence filtering, confidence scores in SimTrade,
and ai_shuffled control mode functionality.
"""
import asyncio
import unittest
from app.config import Settings
from backtest.mock_ai_analyst import MockAiAnalyst
from backtest.simulator import BacktestSimulator
from backtest.data_source import generate_synthetic_history
from backtest.metrics import compute_report


class TestConfidenceAndAI(unittest.TestCase):

    def setUp(self):
        self.settings = Settings(
            min_confidence_score=85,
            require_technical_confirmation=True,
        )
        self.candles = generate_synthetic_history(days=30, timeframe_minutes=15, seed=42)

    def test_sim_trade_stores_confidence(self):
        analyst = MockAiAnalyst(mode="ai_mirror", seed=42, settings_obj=self.settings)
        sim = BacktestSimulator(
            candles=self.candles,
            symbol="BTC/USDT",
            analyst=analyst,
            settings_obj=self.settings,
            initial_equity=10000.0,
        )
        trades = asyncio.run(sim.run())
        if trades:
            for t in trades:
                self.assertIsNotNone(t.ai_confidence, "ai_confidence should be set on SimTrade")
                self.assertGreaterEqual(t.ai_confidence, 85, "Trade confidence must satisfy min_confidence_score")

    def test_confidence_threshold_filter(self):
        # Force min_confidence_score to 95 and verify all trades have confidence >= 95
        strict_settings = Settings(min_confidence_score=95, require_technical_confirmation=True)
        analyst = MockAiAnalyst(mode="ai_mirror", seed=42, settings_obj=strict_settings)
        sim = BacktestSimulator(
            candles=self.candles,
            symbol="BTC/USDT",
            analyst=analyst,
            settings_obj=strict_settings,
            initial_equity=10000.0,
        )
        trades = asyncio.run(sim.run())
        for t in trades:
            self.assertGreaterEqual(t.ai_confidence, 95)

    def test_ai_shuffled_mode(self):
        analyst_shuffled = MockAiAnalyst(mode="ai_shuffled", seed=42)
        sim = BacktestSimulator(
            candles=self.candles,
            symbol="BTC/USDT",
            analyst=analyst_shuffled,
            settings_obj=self.settings,
            initial_equity=10000.0,
        )
        trades = asyncio.run(sim.run())
        # Ensure simulator runs cleanly with ai_shuffled mode
        self.assertIsInstance(trades, list)


if __name__ == "__main__":
    unittest.main()
