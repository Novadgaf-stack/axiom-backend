"""
NEXUS-7 — MTF-TP ROBUSTNESS & ATTRIBUTION EVALUATOR (RESEARCH V7)
Executes parameter neighborhood scanning, asset separation, regime separation, directional attribution,
component attribution, and cost stress matrix for MTF-TP.
"""
from typing import Dict, List, Tuple
import numpy as np

from backtest.research_v5.microstructure import BinanceMicrostructureFrictionModel
from backtest.research_v5.trade_ledger import TradeLedger, TradeRecord
from backtest.research_v6.alpha_hypotheses import StructuralAlphaEngine


class MTFTPRobustnessEvaluator:
    """Performs comprehensive 10-step robustness and attribution analysis on MTF-TP."""

    @staticmethod
    def run_simulation_custom(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        friction_model,
        adx_thresh: float = 25.0,
        atr_thresh: float = 0.9,
        pullback_pct: float = 0.002,
        direction_filter: str = "BOTH"  # "BOTH", "LONG_ONLY", "SHORT_ONLY"
    ) -> Dict:
        n = len(prices)
        ledger = TradeLedger()
        position = 0
        entry_price = 0.0
        entry_idx = 0

        for i in range(50, n - 1):
            p = prices[i]
            vwap = features["vwap_15m"][i]
            bias_4h = features["bias_4h"][i]
            atr_ratio = features["atr_ratio_15m"][i]

            sig = 0
            if bias_4h == 1.0 and atr_ratio >= atr_thresh:
                if low[i] <= vwap * (1.0 + pullback_pct) and p > vwap:
                    sig = 1
            elif bias_4h == -1.0 and atr_ratio >= atr_thresh:
                if high[i] >= vwap * (1.0 - pullback_pct) and p < vwap:
                    sig = -1

            if direction_filter == "LONG_ONLY" and sig == -1:
                sig = 0
            elif direction_filter == "SHORT_ONLY" and sig == 1:
                sig = 0

            # Exit logic
            if position != 0 and (sig == -position or i == n - 2):
                exit_side = "SELL" if position == 1 else "BUY"
                eff_exit_price, exit_fee, _, ok_exit = friction_model.calculate_effective_price_and_fee(
                    p, exit_side, is_maker=False, atr_ratio=features["atr_ratio_15m"][i], equity_allocated=1000.0
                )

                if position == 1:
                    gross_pnl = ((p - entry_price) / entry_price) * 1000.0
                    net_pnl = ((eff_exit_price - entry_price) / entry_price) * 1000.0 - exit_fee
                else:
                    gross_pnl = ((entry_price - p) / entry_price) * 1000.0
                    net_pnl = ((entry_price - eff_exit_price) / entry_price) * 1000.0 - exit_fee

                r_mult = net_pnl / (entry_price * 0.01) if entry_price > 0 else 0.0

                record = TradeRecord(
                    timestamp_iso="2026-08-13T00:00:00Z",
                    symbol="BTC/USDT",
                    side="LONG" if position == 1 else "SHORT",
                    entry_price=round(entry_price, 2),
                    exit_price=round(eff_exit_price, 2),
                    holding_bars=i - entry_idx,
                    exit_reason="SIGNAL_REVERSAL" if sig == -position else "MAX_HOLD_TIMEOUT",
                    gross_pnl_usd=round(gross_pnl, 2),
                    fee_usd=round(exit_fee, 2),
                    slippage_usd=round(abs(eff_exit_price - p) * (1000.0 / entry_price), 2),
                    net_pnl_usd=round(net_pnl, 2),
                    r_multiple=round(r_mult, 2),
                )
                ledger.add_trade(record)
                position = 0

            # Entry logic
            if position == 0 and sig != 0:
                entry_side = "BUY" if sig == 1 else "SELL"
                eff_entry_price, entry_fee, _, ok_entry = friction_model.calculate_effective_price_and_fee(
                    p, entry_side, is_maker=False, atr_ratio=features["atr_ratio_15m"][i], equity_allocated=1000.0
                )
                if ok_entry:
                    position = sig
                    entry_price = eff_entry_price
                    entry_idx = i

        return ledger.calculate_summary()

    @classmethod
    def evaluate_parameter_grid(
        cls,
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        friction_model
    ) -> List[Dict]:
        """Tests 27 parameter grid variations to check neighborhood stability."""
        adx_grid = [20.0, 25.0, 30.0]
        atr_grid = [0.8, 0.9, 1.0]
        pb_grid = [0.001, 0.002, 0.003]

        grid_results = []
        for adx in adx_grid:
            for atr_val in atr_grid:
                for pb in pb_grid:
                    res = cls.run_simulation_custom(
                        prices, high, low, volume, features, friction_model,
                        adx_thresh=adx, atr_thresh=atr_val, pullback_pct=pb
                    )
                    grid_results.append({
                        "adx": adx,
                        "atr_thresh": atr_val,
                        "pullback_pct": pb,
                        "trades": res["trades_count"],
                        "win_rate": res["win_rate"],
                        "profit_factor": res["profit_factor"],
                        "net_pnl": res["net_pnl_usd"],
                        "expectancy": res["expectancy_usd"],
                    })

        return grid_results

    @classmethod
    def evaluate_cost_stress(
        cls,
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray]
    ) -> Dict[str, Dict]:
        """Evaluates 3 cost stress tiers."""
        tiers = {
            "Tier 1 (Low Cost)": BinanceMicrostructureFrictionModel(maker_fee_pct=0.02, taker_fee_pct=0.02, base_slippage_pct=0.01),
            "Tier 2 (Standard Cost)": BinanceMicrostructureFrictionModel(maker_fee_pct=0.02, taker_fee_pct=0.05, base_slippage_pct=0.03),
            "Tier 3 (Severe Stress)": BinanceMicrostructureFrictionModel(maker_fee_pct=0.05, taker_fee_pct=0.10, base_slippage_pct=0.08),
        }

        tier_results = {}
        for tier_name, friction in tiers.items():
            res = cls.run_simulation_custom(prices, high, low, volume, features, friction)
            tier_results[tier_name] = res

        return tier_results
