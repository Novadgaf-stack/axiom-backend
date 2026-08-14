"""
NEXUS-7 — RESEARCH V25 FREQUENCY TARGET MODULE
Calculates detailed trade frequency distribution statistics (median, percentiles, 0-trade days %, >=3-trade days %, max trades/day).
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any


def calculate_frequency_distribution(closed_trades: List[Dict[str, Any]], total_days: int = 730) -> Dict[str, Any]:
    daily_counts: Dict[pd.Timestamp, int] = {}
    for t in closed_trades:
        day = pd.Timestamp(t["entry_time"]).floor("D")
        daily_counts[day] = daily_counts.get(day, 0) + 1
        
    all_days = pd.date_range(end=pd.Timestamp.now(), periods=total_days, freq="D").floor("D")
    counts_list = [daily_counts.get(d, 0) for d in all_days]
    
    avg_daily = len(closed_trades) / total_days if total_days > 0 else 0.0
    median_daily = float(np.median(counts_list))
    p25_daily = float(np.percentile(counts_list, 25))
    p75_daily = float(np.percentile(counts_list, 75))
    pct_zero_days = (counts_list.count(0) / len(counts_list)) * 100.0 if counts_list else 0.0
    pct_ge_3_days = (sum(1 for c in counts_list if c >= 3) / len(counts_list)) * 100.0 if counts_list else 0.0
    max_daily = max(counts_list) if counts_list else 0
    
    return {
        "avg_trades_per_day": round(avg_daily, 2),
        "median_trades_per_day": round(median_daily, 2),
        "p25_trades_per_day": round(p25_daily, 2),
        "p75_trades_per_day": round(p75_daily, 2),
        "pct_zero_trade_days": round(pct_zero_days, 1),
        "pct_ge_3_trade_days": round(pct_ge_3_days, 1),
        "max_trades_per_day": max_daily
    }
