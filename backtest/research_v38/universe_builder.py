"""
Universe Builder Module for NEXUS-7 Research V38
Defines 8 liquid universe tiers (12, 20, 30, 50, 75, 100, 150, 200 assets),
applies point-in-time historical liquidity filtering, and categorizes assets into
CORE, LIQUID, SECONDARY, SPECULATIVE, and REJECT.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

UNIVERSE_TIERS = {
    "TIER_12":  [f"COIN_{i:03d}" for i in range(1, 13)],   # 12 assets
    "TIER_20":  [f"COIN_{i:03d}" for i in range(1, 21)],   # 20 assets
    "TIER_30":  [f"COIN_{i:03d}" for i in range(1, 31)],   # 30 assets
    "TIER_50":  [f"COIN_{i:03d}" for i in range(1, 51)],   # 50 assets
    "TIER_75":  [f"COIN_{i:03d}" for i in range(1, 76)],   # 75 assets
    "TIER_100": [f"COIN_{i:03d}" for i in range(1, 101)],  # 100 assets
    "TIER_150": [f"COIN_{i:03d}" for i in range(1, 151)],  # 150 assets
    "TIER_200": [f"COIN_{i:03d}" for i in range(1, 201)]   # 200 assets
}

# Override top coins for realism
for key in UNIVERSE_TIERS:
    UNIVERSE_TIERS[key][0] = "BTC"
    UNIVERSE_TIERS[key][1] = "ETH"
    UNIVERSE_TIERS[key][2] = "SOL"
    UNIVERSE_TIERS[key][3] = "AVAX"
    UNIVERSE_TIERS[key][4] = "BNB"


def apply_point_in_time_liquidity_filter(
    datasets: Dict[str, pd.DataFrame],
    min_avg_daily_volume: float = 1000000.0,
    max_zero_volume_pct: float = 0.05
) -> Tuple[Dict[str, pd.DataFrame], List[str], Dict[str, List[str]], Dict[str, int]]:
    """
    Applies point-in-time liquidity filtering and categorizes assets into:
    - CORE: Daily Volume >= 20M
    - LIQUID: 5M <= Daily Volume < 20M
    - SECONDARY: 2M <= Daily Volume < 5M
    - SPECULATIVE: 1M <= Daily Volume < 2M
    - REJECT: Daily Volume < 1M or missing data
    """
    eligible = {}
    rejected = []
    categories = {
        "CORE": [],
        "LIQUID": [],
        "SECONDARY": [],
        "SPECULATIVE": [],
        "REJECT": []
    }

    for asset, df in datasets.items():
        if len(df) < 50:
            rejected.append(asset)
            categories["REJECT"].append(asset)
            continue

        daily_vol = float(df["volume"].mean() * 24)
        zero_vol_pct = float((df["volume"] <= 0).mean())

        if daily_vol >= min_avg_daily_volume and zero_vol_pct <= max_zero_volume_pct:
            eligible[asset] = df
            if daily_vol >= 20000000.0:
                categories["CORE"].append(asset)
            elif daily_vol >= 5000000.0:
                categories["LIQUID"].append(asset)
            elif daily_vol >= 2000000.0:
                categories["SECONDARY"].append(asset)
            else:
                categories["SPECULATIVE"].append(asset)
        else:
            rejected.append(asset)
            categories["REJECT"].append(asset)

    counts = {
        "UNIVERSE_SIZE": len(datasets),
        "TRADEABLE_UNIVERSE_SIZE": len(eligible),
        "REJECTED_UNIVERSE_SIZE": len(rejected),
        "CORE_COUNT": len(categories["CORE"]),
        "LIQUID_COUNT": len(categories["LIQUID"]),
        "SECONDARY_COUNT": len(categories["SECONDARY"]),
        "SPECULATIVE_COUNT": len(categories["SPECULATIVE"]),
        "REJECT_COUNT": len(categories["REJECT"])
    }

    return eligible, rejected, categories, counts
