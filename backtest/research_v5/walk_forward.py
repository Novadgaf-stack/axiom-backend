"""
NEXUS-7 — WALK-FORWARD EVALUATOR WITH CANONICAL TRADE LEDGER (RESEARCH V5)
Evaluates strategy ensemble stability using the canonical TradeLedger engine.
"""
from datetime import datetime, timezone
from typing import Dict, List
import numpy as np

from backtest.research_v4.consensus import StrategyConsensusEngine
from backtest.research_v5.features import MultiTimeframeFeatureEngine
from backtest.research_v5.microstructure import BinanceMicrostructureFrictionModel
from backtest.research_v4.regime import RegimeDetector
from backtest.research_v5.trade_ledger import TradeLedger, TradeRecord



class WalkForwardEvaluator:
    """Executes walk-forward evaluation using canonical TradeLedger accounting."""

    def __init__(self, min_confidence: float = 65.0):
        self.min_confidence = min_confidence
        self.consensus_engine = StrategyConsensusEngine()
        self.friction_model = BinanceMicrostructureFrictionModel()

    def run_simulation(
        self,
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        min_confidence: float = 65.0
    ) -> Dict:
        n = len(prices)
        if n < 100:
            ledger = TradeLedger()
            return ledger.calculate_summary()

        features = MultiTimeframeFeatureEngine.compute_features(prices, high, low, volume)
        indicators = RegimeDetector.calculate_indicators(prices, high, low)
        ledger = TradeLedger()

        position = 0
        entry_price = 0.0
        entry_idx = 0

        for i in range(50, n - 1):
            regime = RegimeDetector.detect_regime(
                prices[i],
                indicators["ema50"][i],
                indicators["ema200"][i],
                indicators["atr_ratio"][i],
                indicators["adx"][i]
            )

            res = self.consensus_engine.evaluate_consensus(prices, high, low, volume, regime, i)
            sig = res["signal"]
            conf = res["confidence"]
            current_price = prices[i]

            # Exit logic
            if position != 0 and (sig == -position or i == n - 2):
                exit_side = "SELL" if position == 1 else "BUY"
                eff_exit_price, exit_fee, _, ok_exit = self.friction_model.calculate_effective_price_and_fee(
                    current_price, exit_side, is_maker=False, atr_ratio=features["atr_ratio_15m"][i], equity_allocated=1000.0
                )

                if position == 1:
                    gross_pnl = ((current_price - entry_price) / entry_price) * 1000.0
                    net_pnl = ((eff_exit_price - entry_price) / entry_price) * 1000.0 - exit_fee
                else:
                    gross_pnl = ((entry_price - current_price) / entry_price) * 1000.0
                    net_pnl = ((entry_price - eff_exit_price) / entry_price) * 1000.0 - exit_fee

                r_mult = net_pnl / (entry_price * 0.01) if entry_price > 0 else 0.0

                record = TradeRecord(
                    timestamp_iso=datetime.now(timezone.utc).isoformat(),
                    symbol="BTC/USDT",
                    side="LONG" if position == 1 else "SHORT",
                    entry_price=round(entry_price, 2),
                    exit_price=round(eff_exit_price, 2),
                    holding_bars=i - entry_idx,
                    exit_reason="SIGNAL_REVERSAL" if sig == -position else "MAX_HOLD_TIMEOUT",
                    gross_pnl_usd=round(gross_pnl, 2),
                    fee_usd=round(exit_fee, 2),
                    slippage_usd=round(abs(eff_exit_price - current_price) * (1000.0 / entry_price), 2),
                    net_pnl_usd=round(net_pnl, 2),
                    r_multiple=round(r_mult, 2),
                )
                ledger.add_trade(record)
                position = 0

            # Entry logic
            if position == 0 and sig != 0 and conf >= min_confidence:
                entry_side = "BUY" if sig == 1 else "SELL"
                eff_entry_price, entry_fee, _, ok_entry = self.friction_model.calculate_effective_price_and_fee(
                    current_price, entry_side, is_maker=False, atr_ratio=features["atr_ratio_15m"][i], equity_allocated=1000.0
                )
                if ok_entry:
                    position = sig
                    entry_price = eff_entry_price
                    entry_idx = i

        return ledger.calculate_summary()

    def evaluate_walk_forward_and_holdout(
        self,
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        n_windows: int = 4
    ) -> Dict:
        n = len(prices)
        split_idx = int(n * 0.70)

        is_prices, is_high, is_low, is_vol = prices[:split_idx], high[:split_idx], low[:split_idx], volume[:split_idx]
        oos_prices, oos_high, oos_low, oos_vol = prices[split_idx:], high[split_idx:], low[split_idx:], volume[split_idx:]

        window_size = len(is_prices) // n_windows
        window_results = []

        for w in range(n_windows):
            w_start = w * window_size
            w_end = (w + 1) * window_size if w < n_windows - 1 else len(is_prices)
            w_res = self.run_simulation(is_prices[w_start:w_end], is_high[w_start:w_end], is_low[w_start:w_end], is_vol[w_start:w_end], self.min_confidence)
            w_res["window"] = w + 1
            window_results.append(w_res)

        oos_res = self.run_simulation(oos_prices, oos_high, oos_low, oos_vol, self.min_confidence)
        profitable_windows = sum(1 for r in window_results if r.get("net_pnl_usd", 0) > 0)

        return {
            "walk_forward_windows": window_results,
            "profitable_wf_windows": profitable_windows,
            "total_wf_windows": n_windows,
            "untouched_oos_holdout": oos_res,
            "overall_is_metrics": self.run_simulation(is_prices, is_high, is_low, is_vol, self.min_confidence),
        }
