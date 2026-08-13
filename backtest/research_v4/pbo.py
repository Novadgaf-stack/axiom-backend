"""
NEXUS-7 — PROBABILITY OF BACKTEST OVERFITTING & BUY-AND-HOLD BENCHMARK (RESEARCH V4)
Calculates PBO, Sharpe/Sortino/Calmar ratios, Monte Carlo trade order resampling,
and benchmarks strategy performance directly against Buy-and-Hold (B&H).
"""
from typing import Dict, List
import numpy as np


class OverfittingAuditor:
    """Calculates PBO score and benchmarks performance against Buy-and-Hold."""

    @staticmethod
    def calculate_buy_and_hold(prices: np.ndarray, initial_equity: float = 10_000.0) -> Dict:
        if len(prices) < 2:
            return {"bh_return_pct": 0.0, "bh_net_pnl": 0.0, "bh_max_dd_pct": 0.0}

        start_p = prices[0]
        end_p = prices[-1]
        bh_return_pct = ((end_p - start_p) / start_p) * 100.0
        bh_net_pnl = initial_equity * (bh_return_pct / 100.0)

        # Max drawdown of Buy and Hold
        peak = prices[0]
        max_dd = 0.0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

        return {
            "bh_return_pct": round(bh_return_pct, 2),
            "bh_net_pnl": round(bh_net_pnl, 2),
            "bh_max_dd_pct": round(max_dd, 1),
        }

    @staticmethod
    def calculate_ratios(net_pnl: float, max_dd_pct: float, win_rate_pct: float, trades: int) -> Dict:
        if trades == 0 or max_dd_pct == 0:
            return {"sharpe": 0.0, "sortino": 0.0, "calmar": 0.0}

        ret_pct = (net_pnl / 10_000.0) * 100.0
        calmar = ret_pct / max_dd_pct if max_dd_pct > 0 else 0.0

        # Proxy estimate for Sharpe and Sortino from trade distribution
        sharpe_proxy = (win_rate_pct - 50.0) / 25.0
        sortino_proxy = sharpe_proxy * 1.35 if sharpe_proxy > 0 else sharpe_proxy * 0.8

        return {
            "sharpe": round(max(-3.0, min(5.0, sharpe_proxy)), 2),
            "sortino": round(max(-3.0, min(5.0, sortino_proxy)), 2),
            "calmar": round(max(-3.0, min(5.0, calmar)), 2),
        }

    @classmethod
    def evaluate_pbo(cls, wf_results: Dict, n_resamples: int = 500) -> Dict:
        """
        Calculates PBO score based on walk-forward window consistency & Monte Carlo resampling.
        """
        wf_windows = wf_results.get("walk_forward_windows", [])
        total_w = len(wf_windows)
        if total_w == 0:
            return {"pbo_pct": 100.0, "verdict": "HIGH OVERFITTING RISK"}

        pnls = [w["net_pnl"] for w in wf_windows]
        losses_count = sum(1 for p in pnls if p <= 0)
        pbo_pct = (losses_count / total_w) * 100.0

        # Monte Carlo resampling test
        np.random.seed(42)
        simulated_losses = 0
        for _ in range(n_resamples):
            sampled_pnls = np.random.choice(pnls, size=total_w, replace=True)
            if np.sum(sampled_pnls) <= 0:
                simulated_losses += 1

        mc_pbo_pct = (simulated_losses / n_resamples) * 100.0
        final_pbo = max(pbo_pct, mc_pbo_pct)

        if final_pbo < 25.0:
            verdict = "LOW OVERFITTING RISK"
        elif final_pbo < 50.0:
            verdict = "MODERATE OVERFITTING RISK"
        else:
            verdict = "HIGH OVERFITTING RISK — NO PROVEN EDGE"

        return {
            "pbo_pct": round(final_pbo, 1),
            "window_pbo_pct": round(pbo_pct, 1),
            "monte_carlo_pbo_pct": round(mc_pbo_pct, 1),
            "verdict": verdict,
        }
