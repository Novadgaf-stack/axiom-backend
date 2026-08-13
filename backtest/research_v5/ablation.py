"""
NEXUS-7 — ABLATION & COMPONENT SENSITIVITY AUDITOR (RESEARCH V5)
Evaluates incremental component contribution to OOS expectancy and discards non-contributing features.
"""
from typing import Dict, List, Tuple
import numpy as np


class AblationAuditor:
    """Evaluates component contribution across incremental feature steps."""

    @staticmethod
    def run_ablation_study(
        prices: np.ndarray,
        features: Dict[str, np.ndarray],
        friction_model
    ) -> List[Dict]:
        n = len(prices)
        steps = [
            ("Baseline Signal", False, False, False, False),
            ("+ Regime Filter", True, False, False, False),
            ("+ Volume Imbalance", True, True, False, False),
            ("+ MTF 4H Macro Bias", True, True, True, False),
            ("+ Volatility Squeeze", True, True, True, True),
        ]

        results = []
        prev_expectancy = -999.0

        for step_name, use_regime, use_vol, use_mtf, use_squeeze in steps:
            equity = 10_000.0
            trades = []

            for i in range(100, n - 1):
                p = prices[i]

                # Base signal logic
                raw_sig = 1 if features["roc_12_15m"][i] > 1.5 else (-1 if features["roc_12_15m"][i] < -1.5 else 0)
                if raw_sig == 0:
                    continue

                # Incremental filters
                if use_regime and features["atr_ratio_15m"][i] < 0.8:
                    continue
                if use_vol and features["volume_imbalance"][i] < 1.1:
                    continue
                if use_mtf and features["bias_4h"][i] != raw_sig:
                    continue
                if use_squeeze and features["atr_ratio_15m"][i] < 1.3:
                    continue

                # Execute friction model check
                eff_price, fee_usd, qty, ok = friction_model.calculate_effective_price_and_fee(
                    p, "BUY" if raw_sig == 1 else "SELL", is_maker=False, atr_ratio=features["atr_ratio_15m"][i], equity_allocated=1000.0
                )
                if not ok:
                    continue

                next_p = prices[min(n - 1, i + 12)]
                pnl = ((next_p - eff_price) / eff_price * 1000.0) if raw_sig == 1 else ((eff_price - next_p) / eff_price * 1000.0)
                pnl -= fee_usd
                trades.append(pnl)

            expectancy = (sum(trades) / len(trades)) if len(trades) > 0 else 0.0
            win_rate = (sum(1 for t in trades if t > 0) / len(trades) * 100.0) if len(trades) > 0 else 0.0
            
            contributed = (expectancy > prev_expectancy) if prev_expectancy != -999.0 else True
            prev_expectancy = expectancy

            results.append({
                "step_name": step_name,
                "trades": len(trades),
                "win_rate": round(win_rate, 1),
                "expectancy_usd": round(expectancy, 2),
                "net_pnl_usd": round(sum(trades), 2),
                "contribution": "RETAIN" if contributed else "DISCARD",
            })

        return results
