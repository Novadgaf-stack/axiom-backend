"""
Opportunity Generator Module for NEXUS-7 Research V36
Generates structured candidate opportunity dictionaries across multi-asset datasets and timeframes (15m, 30m, 1h, 4h).
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v36.feature_engine import extract_signal_features
from backtest.research_v36.market_regime import classify_market_regime


def generate_candidate_opportunities(
    datasets: Dict[str, pd.DataFrame],
    strategy_fn: Any,
    family_name: str = "momentum_cont",
    timeframe: str = "1h"
) -> List[Dict[str, Any]]:
    """
    Scans asset datasets and constructs structured opportunity dictionaries.
    """
    opportunities = []

    for asset, df in datasets.items():
        df_sig = strategy_fn(df)
        non_zero_sigs = df_sig[df_sig["signal"] != 0]

        for idx, row in non_zero_sigs.iterrows():
            bar_idx = int(df.index.get_loc(idx)) if idx in df.index else 0
            sig_dir = int(row["signal"])
            entry = float(row["close"])
            stop = float(row["stop_loss"])
            target = float(row["take_profit"])

            features = extract_signal_features(df, bar_idx, sig_dir, entry, stop, target)
            regime = classify_market_regime(df, bar_idx)

            opportunities.append({
                "timestamp": row["timestamp"],
                "asset": asset,
                "strategy_family": family_name,
                "timeframe": timeframe,
                "direction": "LONG" if sig_dir == 1 else "SHORT",
                "signal_dir": sig_dir,
                "entry_price": entry,
                "stop_loss": stop,
                "take_profit": target,
                "rr_ratio": features["rr_ratio"],
                "stop_distance": abs(entry - stop),
                "market_regime": regime,
                "liquidity_state": "HIGH_LIQUIDITY",
                "volatility_state": features["volatility_regime"],
                "momentum_state": features["momentum_strength"],
                "trend_state": features["trend_quality"],
                "confidence": float(row.get("confidence", 0.50)),
                "features": features,
                "risk_pct": 0.0050
            })

    return opportunities
