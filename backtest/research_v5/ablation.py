"""
NEXUS-7 — ABLATION & COMPONENT SENSITIVITY AUDITOR (RESEARCH V5)
Evaluates incremental component contribution using canonical TradeLedger accounting and StrategyConsensusEngine.
"""
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import numpy as np

from backtest.research_v4.consensus import StrategyConsensusEngine
from backtest.research_v4.regime import RegimeDetector
from backtest.research_v5.trade_ledger import TradeLedger, TradeRecord



class AblationAuditor:
    """Evaluates component contribution across incremental feature steps using canonical TradeLedger."""

    @staticmethod
    def run_ablation_study(
        prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        features: Dict[str, np.ndarray],
        friction_model,
        min_confidence: float = 65.0
    ) -> List[Dict]:
        n = len(prices)
        indicators = RegimeDetector.calculate_indicators(prices, high, low)
        consensus_engine = StrategyConsensusEngine()

        steps = [
            ("Baseline Consensus", False, False, False, False),
            ("+ Regime Filter", True, False, False, False),
            ("+ Volume Imbalance", True, True, False, False),
            ("+ MTF 4H Macro Bias", True, True, True, False),
            ("+ Volatility Squeeze", True, True, True, True),
        ]

        results = []
        prev_expectancy = -999.0

        for step_name, use_regime, use_vol, use_mtf, use_squeeze in steps:
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

                res = consensus_engine.evaluate_consensus(prices, high, low, volume, regime, i)
                sig = res["signal"]
                conf = res["confidence"]
                current_price = prices[i]

                # Incremental ablation gates
                if sig != 0:
                    if use_regime and features["atr_ratio_15m"][i] < 0.8:
                        sig = 0
                    if use_vol and features["volume_imbalance"][i] < 1.1:
                        sig = 0
                    if use_mtf and features["bias_4h"][i] != sig:
                        sig = 0
                    if use_squeeze and features["atr_ratio_15m"][i] < 1.3:
                        sig = 0

                # Exit logic
                if position != 0 and (sig == -position or i == n - 2):
                    exit_side = "SELL" if position == 1 else "BUY"
                    eff_exit_price, exit_fee, _, ok_exit = friction_model.calculate_effective_price_and_fee(
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
                    eff_entry_price, entry_fee, _, ok_entry = friction_model.calculate_effective_price_and_fee(
                        current_price, entry_side, is_maker=False, atr_ratio=features["atr_ratio_15m"][i], equity_allocated=1000.0
                    )
                    if ok_entry:
                        position = sig
                        entry_price = eff_entry_price
                        entry_idx = i

            summary = ledger.calculate_summary()
            expectancy = summary["expectancy_usd"]
            contributed = (expectancy > prev_expectancy) if prev_expectancy != -999.0 else True
            prev_expectancy = expectancy

            results.append({
                "step_name": step_name,
                "trades": summary["trades_count"],
                "win_rate": summary["win_rate"],
                "expectancy_usd": summary["expectancy_usd"],
                "net_pnl_usd": summary["net_pnl_usd"],
                "profit_factor": summary["profit_factor"],
                "contribution": "RETAIN" if contributed else "DISCARD",
            })

        return results
