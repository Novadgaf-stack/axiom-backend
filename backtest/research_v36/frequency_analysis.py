"""
Frequency Analysis Module for NEXUS-7 Research V36
Calculates detailed daily participation statistics:
avg trades/day, median trades/day, 90th percentile trades/day, max trades/day,
% of days participating (target >=70%), % of days with 0 trades, longest no-trade streak.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def analyze_daily_participation(
    trades: List[Dict[str, Any]],
    total_days: float = 90.0
) -> Dict[str, Any]:
    """
    Computes rigorous daily opportunity and participation metrics.
    """
    if not trades:
        return {
            "avg_trades_per_day": 0.0,
            "median_trades_per_day": 0.0,
            "p90_trades_per_day": 0.0,
            "max_trades_per_day": 0,
            "pct_days_traded": 0.0,
            "pct_days_no_trade": 100.0,
            "longest_no_trade_streak_days": int(total_days),
            "total_days_evaluated": int(total_days),
            "participation_category": "LOW"
        }

    df_tr = pd.DataFrame(trades)
    df_tr["date"] = pd.to_datetime(df_tr["entry_time"]).dt.date

    daily_counts = df_tr.groupby("date").size()
    total_days_int = int(total_days)

    days_with_trades = len(daily_counts)
    days_no_trades = max(0, total_days_int - days_with_trades)

    all_daily_counts = np.zeros(total_days_int)
    for idx, count in enumerate(daily_counts.values[:total_days_int]):
        all_daily_counts[idx] = count

    avg_tpd = float(np.mean(all_daily_counts))
    median_tpd = float(np.median(all_daily_counts))
    p90_tpd = float(np.percentile(all_daily_counts, 90))
    max_tpd = int(np.max(all_daily_counts))

    pct_days_traded = (days_with_trades / max(1, total_days_int)) * 100.0
    pct_days_no_trade = (days_no_trades / max(1, total_days_int)) * 100.0

    longest_streak = 0
    curr_streak = 0
    for cnt in all_daily_counts:
        if cnt == 0:
            curr_streak += 1
            if curr_streak > longest_streak:
                longest_streak = curr_streak
        else:
            curr_streak = 0

    if avg_tpd >= 1.0:
        cat = "HIGH-FREQUENCY"
    elif avg_tpd >= 0.75:
        cat = "FREQUENT"
    elif avg_tpd >= 0.50:
        cat = "MODERATE"
    else:
        cat = "LOW"

    return {
        "avg_trades_per_day": round(avg_tpd, 2),
        "median_trades_per_day": round(median_tpd, 2),
        "p90_trades_per_day": round(p90_tpd, 2),
        "max_trades_per_day": max_tpd,
        "pct_days_traded": round(pct_days_traded, 1),
        "pct_days_no_trade": round(pct_days_no_trade, 1),
        "longest_no_trade_streak_days": longest_streak,
        "total_days_evaluated": total_days_int,
        "participation_category": cat
    }
