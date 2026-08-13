"""
NEXUS-7 — WALK-FORWARD EVALUATOR WITH UNTOUCHED OOS (RESEARCH V4)
Evaluates strategy ensemble stability across rolling walk-forward windows
and enforces an untouched 30% holdout Out-of-Sample (OOS) test set.
"""
from typing import Dict, List, Tuple
import numpy as np
from backtest.research_v4.regime import RegimeDetector
from backtest.research_v4.consensus import StrategyConsensusEngine


class WalkForwardEvaluator:
    """Executes walk-forward evaluation with strict out-of-sample temporal locking."""

    def __init__(self, fee_pct: float = 0.1, slippage_pct: float = 0.05):
        self.fee_pct = fee_pct / 100.0
        self.slippage_pct = slippage_pct / 100.0
        self.consensus_engine = StrategyConsensusEngine()

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
            return {
                "trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "net_pnl": 0.0,
                "max_dd_pct": 0.0,
                "expectancy": 0.0,
            }

        indicators = RegimeDetector.calculate_indicators(prices, high, low)
        equity = 10_000.0
        equity_curve = [equity]
        position = 0
        entry_price = 0.0
        trades = []

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
            if position == 1 and (sig == -1 or i == n - 2):
                exit_price = current_price * (1.0 - self.slippage_pct)
                pnl = (exit_price - entry_price) / entry_price * equity
                pnl -= equity * (self.fee_pct * 2)
                equity += pnl
                trades.append(pnl)
                position = 0
            elif position == -1 and (sig == 1 or i == n - 2):
                exit_price = current_price * (1.0 + self.slippage_pct)
                pnl = (entry_price - exit_price) / entry_price * equity
                pnl -= equity * (self.fee_pct * 2)
                equity += pnl
                trades.append(pnl)
                position = 0

            # Entry logic
            if position == 0 and sig != 0 and conf >= min_confidence:
                position = sig
                entry_price = current_price * (1.0 + self.slippage_pct if sig == 1 else 1.0 - self.slippage_pct)

            equity_curve.append(equity)

        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
        win_rate = (len(wins) / len(trades) * 100.0) if len(trades) > 0 else 0.0
        expectancy = (sum(trades) / len(trades)) if len(trades) > 0 else 0.0

        # Drawdown
        peak = equity_curve[0]
        max_dd = 0.0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

        return {
            "trades": len(trades),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "net_pnl": round(equity - 10_000.0, 2),
            "max_dd_pct": round(max_dd, 1),
            "expectancy": round(expectancy, 2),
        }

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

        # In-Sample & Walk-Forward Evaluation (First 70%)
        is_prices = prices[:split_idx]
        is_high = high[:split_idx]
        is_low = low[:split_idx]
        is_vol = volume[:split_idx]

        window_size = len(is_prices) // n_windows
        window_results = []

        for w in range(n_windows):
            w_start = w * window_size
            w_end = (w + 1) * window_size if w < n_windows - 1 else len(is_prices)
            w_res = self.run_simulation(
                is_prices[w_start:w_end],
                is_high[w_start:w_end],
                is_low[w_start:w_end],
                is_vol[w_start:w_end]
            )
            w_res["window"] = w + 1
            window_results.append(w_res)

        # Untouched Out-of-Sample Holdout Evaluation (Last 30%)
        oos_prices = prices[split_idx:]
        oos_high = high[split_idx:]
        oos_low = low[split_idx:]
        oos_vol = volume[split_idx:]

        oos_res = self.run_simulation(oos_prices, oos_high, oos_low, oos_vol)

        profitable_windows = sum(1 for r in window_results if r["net_pnl"] > 0)

        return {
            "walk_forward_windows": window_results,
            "profitable_wf_windows": profitable_windows,
            "total_wf_windows": n_windows,
            "untouched_oos_holdout": oos_res,
            "overall_is_metrics": self.run_simulation(is_prices, is_high, is_low, is_vol),
        }
