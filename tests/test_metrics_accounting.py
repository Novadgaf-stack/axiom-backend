"""
Unit tests for metrics accounting, transaction cost deduction, and Sharpe/Sortino/Calmar calculations.
"""
import unittest
from backtest.metrics import SimTrade, compute_report


class TestMetricsAccounting(unittest.TestCase):

    def test_fee_and_slippage_accounting(self):
        # Create 2 synthetic trade records with known fees and PnL
        t1 = SimTrade(
            symbol="BTC/USDT",
            entry_index=10,
            entry_time_ms=1000,
            entry_price=50000.0,
            quantity=0.1,
            stop_loss=49000.0,
            take_profit=52000.0,
            risk_usd=100.0,
            ai_confidence=90,
            exit_index=15,
            exit_time_ms=2000,
            exit_price=52000.0,
            exit_reason="TAKE_PROFIT",
            fees_usd=10.20,
            slippage_usd=5.10,
            pnl_usd=184.70,  # Net PnL after costs
        )

        t2 = SimTrade(
            symbol="BTC/USDT",
            entry_index=20,
            entry_time_ms=3000,
            entry_price=50000.0,
            quantity=0.1,
            stop_loss=49000.0,
            take_profit=52000.0,
            risk_usd=100.0,
            ai_confidence=88,
            exit_index=25,
            exit_time_ms=4000,
            exit_price=49000.0,
            exit_reason="STOP_LOSS",
            fees_usd=9.90,
            slippage_usd=4.95,
            pnl_usd=-114.85, # Net loss including costs
        )

        report = compute_report(
            trades=[t1, t2],
            initial_equity=10000.0,
            mode="test",
            symbol="BTC/USDT",
            timeframe="15m",
            total_candles=1000,
            ai_calls_made=2,
        )

        self.assertAlmostEqual(report.total_fees_usd, 20.10, places=2)
        self.assertAlmostEqual(report.total_slippage_usd, 10.05, places=2)
        self.assertAlmostEqual(report.net_pnl_usd, 69.85, places=2)
        self.assertEqual(report.total_trades, 2)
        self.assertEqual(report.winning_trades, 1)
        self.assertEqual(report.losing_trades, 1)
        self.assertAlmostEqual(report.win_rate_pct, 50.0, places=1)
        self.assertAlmostEqual(report.profit_factor, 184.70 / 114.85, places=2)

    def test_empty_trades_handling(self):
        report = compute_report(
            trades=[],
            initial_equity=10000.0,
            mode="test",
            symbol="BTC/USDT",
            timeframe="15m",
            total_candles=1000,
            ai_calls_made=0,
        )
        self.assertEqual(report.total_trades, 0)
        self.assertEqual(report.net_pnl_usd, 0.0)
        self.assertEqual(report.profit_factor, 0.0)
        self.assertEqual(report.sharpe_ratio, 0.0)


if __name__ == "__main__":
    unittest.main()
