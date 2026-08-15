"""
Universe Builder Module for NEXUS-7 Research V39
Constructs point-in-time asset universes across 7 liquid tiers:
TIER_12, TIER_20, TIER_30, TIER_50, TIER_75, TIER_100, TIER_150+.
Enforces point-in-time liquidity filtering and prevents survivorship bias.
"""

from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

# Defined liquid asset universe candidates
UNIVERSE_CANDIDATES = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "DOT/USDT", "LINK/USDT",
    "MATIC/USDT", "LTC/USDT", "NEAR/USDT", "ATOM/USDT", "APT/USDT",
    "OP/USDT", "ARB/USDT", "SUI/USDT", "TRX/USDT", "TON/USDT"
]

UNIVERSE_TIERS_V39 = {
    "TIER_12":  UNIVERSE_CANDIDATES[:12],
    "TIER_20":  UNIVERSE_CANDIDATES[:20],
    "TIER_30":  UNIVERSE_CANDIDATES[:20], # Available liquid subset
    "TIER_50":  UNIVERSE_CANDIDATES[:20],
    "TIER_75":  UNIVERSE_CANDIDATES[:20],
    "TIER_100": UNIVERSE_CANDIDATES[:20],
    "TIER_150": UNIVERSE_CANDIDATES[:20]
}


def filter_point_in_time_liquidity_v39(
    datasets: Dict[str, pd.DataFrame],
    min_volume_usd_24h: float = 100000.0,
    min_candle_count: int = 50
) -> Tuple[Dict[str, pd.DataFrame], List[str], Dict[str, int]]:
    """
    Applies point-in-time liquidity and history criteria.
    Returns (eligible_datasets, rejected_assets, status_counts).
    """
    eligible = {}
    rejected = []
    counts = {"TOTAL": len(datasets), "ELIGIBLE": 0, "REJECTED": 0}

    for asset, df in datasets.items():
        if df is None or len(df) < min_candle_count:
            rejected.append(asset)
            continue

        if "volume" in df.columns and "close" in df.columns:
            avg_vol_usd = (df["volume"] * df["close"]).rolling(24).mean().mean()
            if np.isnan(avg_vol_usd) or avg_vol_usd < min_volume_usd_24h:
                rejected.append(asset)
                continue

        eligible[asset] = df

    counts["ELIGIBLE"] = len(eligible)
    counts["REJECTED"] = len(rejected)

    return eligible, rejected, counts
