"""
Unit tests for the Backtest Simulator and Metrics Engine.
"""
import unittest
from datetime import datetime, timezone
import numpy as np

from app.config import Settings
from app.indicators import compute_snapshot
from app.risk import RiskManager, TradePlan
from backtest.mock_ai_analyst import MockAiAnalyst
from backtest.simulator import BacktestSimulator
from backtest.metrics import SimTrade, compute_report


class TestSimulatorIntegrity(unittest.TestCase):

    def setUp(self):
        self.settings = Settings(
            atr_period=14,
            atr_sl_multiplier=1.5,
            t1_tp_multiplier=1.0,
            t2_tp_multiplier=2.5,
            min_volume_ratio=0.8,
            min_adx=20.0,
            enable_multi_stage_exits=True,
        )

    def _generate_mock_candles(self, count=100, base_price=50000.0):
        candles = []
        now_ms = 1600000000000
        tf_ms = 15 * 60 * 1000
        price = base_price
        for i in range(count):
            o = price
            c = price + (10.0 if i % 2 == 0 else -8.0)
            h = max(o, c) + 15.0
            l = min(o, c) - 15.0
            v = 100.0 + (i * 2)
            candles.append([now_ms + i * tf_ms, round(o, 2), round(h, 2), round(l, 2), round(c, 2), round(v, 2)])
            price = c
        return candles

    def test_look_ahead_bias_discipline(self):
        candles = self._generate_mock_candles(count=60)
        sim = BacktestSimulator(
            candles=candles,
            symbol="BTC/USDT",
            analyst=MockAiAnalyst(mode="technical_only"),
            settings_obj=self.settings,
        )
        window = sim._window(40)
        # Window must contain 41 candles + 1 placeholder row
        self.assertEqual(len(window), 42)
        self.assertEqual(window[-1], window[-2])  # last row is identical placeholder

    def test_same_bar_sl_tp_conflict_conservative(self):
        # Entry at 50000, SL=49000, TP=52000
        plan = TradePlan(
            symbol="BTC/USDT",
            side="buy",
            quantity=1.0,
            entry_price_estimate=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            notional_usd=50000.0,
            risk_usd=1000.0,
            tp1_price=51000.0,
            tp2_price=53000.0,
            tranche1_qty=0.5,
            tranche2_qty=0.5,
        )

        candles = [
            [1600000000000, 50000, 50100, 49900, 50000, 100],  # index 0 (signal)
            [1600000000000 + 15 * 60000, 50000, 50100, 49900, 50000, 100],  # index 1 (entry open)
            [1600000000000 + 30 * 60000, 50000, 54000, 48000, 50000, 100],  # index 2 (touches BOTH SL 49k and TP 52k)
        ]

        sim = BacktestSimulator(
            candles=candles,
            symbol="BTC/USDT",
            analyst=MockAiAnalyst(mode="technical_only"),
            settings_obj=self.settings,
            slippage_pct=0.0,
            fee_pct=0.0,
            same_bar_conflict="conservative",
        )

        # Single stage simulation verification
        self.settings = Settings(enable_multi_stage_exits=False)
        sim.settings = self.settings
        trade, exit_idx = sim._simulate_trade(plan, entry_index=1)
        self.assertEqual(trade.exit_reason, "stop_loss_same_bar_ambiguous")
        self.assertEqual(trade.exit_price, 49000.0)

    def test_fee_and_slippage_calculation(self):
        plan = TradePlan(
            symbol="BTC/USDT",
            side="buy",
            quantity=1.0,
            entry_price_estimate=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            notional_usd=50000.0,
            risk_usd=1000.0,
        )

        candles = [
            [1600000000000, 50000, 50100, 49900, 50000, 100],
            [1600000000000 + 15 * 60000, 50000, 50100, 49900, 50000, 100],
            [1600000000000 + 30 * 60000, 50000, 53000, 49900, 52000, 100],  # TP hit
        ]

        sim = BacktestSimulator(
            candles=candles,
            symbol="BTC/USDT",
            analyst=MockAiAnalyst(mode="technical_only"),
            settings_obj=Settings(enable_multi_stage_exits=False),
            slippage_pct=0.1,  # 0.1%
            fee_pct=0.1,       # 0.1%
        )

        trade, _ = sim._simulate_trade(plan, entry_index=1)
        # Entry price with 0.1% slippage = 50000 * 1.001 = 50050
        # Entry fee = 50050 * 1.0 * 0.001 = 50.05
        # Exit price before slippage = 52000
        # Exit price after 0.1% slippage = 52000 * (1 - 0.001) = 51948
        # Exit fee = 51948 * 1.0 * 0.001 = 51.948
        # Total fees = 50.05 + 51.948 = 101.998
        # Gross PnL = (51948 - 50050) * 1.0 = 1898.0
        # Net PnL = 1898.0 - 101.998 = 1796.002
        self.assertAlmostEqual(trade.entry_price, 50050.0, places=2)
        self.assertAlmostEqual(trade.fees_usd, 101.998, places=2)
        self.assertAlmostEqual(trade.pnl_usd, 1796.002, places=2)

    def test_metrics_computation(self):
        trades = [
            SimTrade(symbol="BTC/USDT", entry_index=1, entry_time_ms=1000, entry_price=50000, quantity=1, stop_loss=49000, take_profit=52000, risk_usd=1000, exit_index=2, exit_time_ms=2000, exit_price=52000, exit_reason="tp", fees_usd=10, slippage_usd=5, pnl_usd=2000),
            SimTrade(symbol="BTC/USDT", entry_index=3, entry_time_ms=3000, entry_price=50000, quantity=1, stop_loss=49000, take_profit=52000, risk_usd=1000, exit_index=4, exit_time_ms=4000, exit_price=49000, exit_reason="sl", fees_usd=10, slippage_usd=5, pnl_usd=-1000),
        ]
        report = compute_report(
            trades=trades,
            initial_equity=10000.0,
            mode="test",
            symbol="BTC/USDT",
            timeframe="15m",
            total_candles=100,
            ai_calls_made=5,
        )

        self.assertEqual(report.total_trades, 2)
        self.assertEqual(report.winning_trades, 1)
        self.assertEqual(report.losing_trades, 1)
        self.assertEqual(report.win_rate_pct, 50.0)
        self.assertEqual(report.net_pnl_usd, 1000.0)
        self.assertEqual(report.profit_factor, 2.0)
        self.assertEqual(report.expectancy_usd, 500.0)
        self.assertEqual(report.expectancy_r, 0.5)


if __name__ == "__main__":
    unittest.main()
