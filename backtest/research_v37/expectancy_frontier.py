"""
Expectancy & Frequency Frontier Analysis Module for NEXUS-7 Research V37
Analyzes performance across frequency frontier bands (0.25 to 3.00+ trades/day)
and measures daily participation metrics (% days traded, mean/median/p90 trades/day, longest zero-trade streak).
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def compute_daily_participation_metrics(
    trades: List[Dict[str, Any]],
    dataset_start_date: pd.Timestamp,
    dataset_end_date: pd.Timestamp
) -> Dict[str, Any]:
    """
    Computes daily participation metrics:
    - signals/day, qualified opps/day, executed trades/day
    - % days with >=1, >=2, >=3 opportunities
    - mean/median/p90 trades/day
    - longest zero-trade streak
    """
    if not dataset_start_date or not dataset_end_date:
        return {
            "avg_trades_per_day": 0.0,
            "median_trades_per_day": 0.0,
            "p90_trades_per_day": 0.0,
            "days_traded_pct": 0.0,
            "days_no_trade_pct": 100.0,
            "longest_no_trade_streak_days": 0,
            "participation_category": "NONE"
        }

    all_days = pd.date_range(start=dataset_start_date.date(), end=dataset_end_date.date(), freq="D")
    total_days = max(1, len(all_days))

    if not trades:
        return {
            "avg_trades_per_day": 0.0,
            "median_trades_per_day": 0.0,
            "p90_trades_per_day": 0.0,
            "days_traded_pct": 0.0,
            "days_no_trade_pct": 100.0,
            "longest_no_trade_streak_days": total_days,
            "participation_category": "NONE"
        }

    trade_dates = [pd.to_datetime(t["entry_time"]).date() for t in trades]
    counts_by_day = pd.Series(trade_dates).value_counts().reindex(all_days.date, fill_value=0)

    avg_tpd = float(counts_by_day.mean())
    median_tpd = float(counts_by_day.median())
    p90_tpd = float(counts_by_day.quantile(0.90))

    days_with_trades = int((counts_by_day > 0).sum())
    days_traded_pct = (days_with_trades / total_days) * 100.0
    days_no_trade_pct = 100.0 - days_traded_pct

    # Longest zero-trade streak
    is_zero = (counts_by_day == 0).astype(int).values
    max_zero_streak = 0
    current_streak = 0
    for z in is_zero:
        if z == 1:
            current_streak += 1
            if current_streak > max_zero_streak:
                max_zero_streak = current_streak
        else:
            current_streak = 0

    if days_traded_pct >= 70.0:
        cat = "HIGH_DAILY_PARTICIPATION"
    elif days_traded_pct >= 40.0:
        cat = "MODERATE_PARTICIPATION"
    elif days_traded_pct > 0.0:
        cat = "LOW_PARTICIPATION"
    else:
        cat = "NO_PARTICIPATION"

    return {
        "avg_trades_per_day": round(avg_tpd, 2),
        "median_trades_per_day": round(median_tpd, 2),
        "p90_trades_per_day": round(p90_tpd, 2),
        "days_traded_pct": round(days_traded_pct, 1),
        "days_no_trade_pct": round(days_no_trade_pct, 1),
        "longest_no_trade_streak_days": max_zero_streak,
        "participation_category": cat
    }


def compute_frequency_frontier_bands(
    all_candidate_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Constructs Frequency Frontier Band summary across 0.25 to 3.00+ trades/day targets.
    """
    bands = [
        ("0.25_TRADES_DAY", 0.0, 0.35),
        ("0.50_TRADES_DAY", 0.35, 0.65),
        ("0.75_TRADES_DAY", 0.65, 0.85),
        ("1.00_TRADES_DAY", 0.85, 1.15),
        ("1.25_TRADES_DAY", 1.15, 1.35),
        ("1.50_TRADES_DAY", 1.35, 1.75),
        ("2.00_TRADES_DAY", 1.75, 2.25),
        ("2.50_TRADES_DAY", 2.25, 2.75),
        ("3.00_PLUS_TRADES_DAY", 2.75, 99.0)
    ]

    summary = []
    for label, min_freq, max_freq in bands:
        matching = [c for c in all_candidate_results if min_freq <= c.get("trades_per_day", 0.0) < max_freq]
        if matching:
            best_candidate = max(matching, key=lambda x: x.get("profit_factor", 0.0))
            summary.append({
                "frequency_band": label,
                "best_strategy": best_candidate["strategy_name"],
                "trades_per_day": best_candidate["trades_per_day"],
                "profit_factor": best_candidate["profit_factor"],
                "net_expectancy": best_candidate["net_expectancy"],
                "bootstrap_ci": str(best_candidate.get("bootstrap_ci", [0, 0])),
                "max_drawdown_pct": best_candidate["max_drawdown_pct"],
                "walk_forward_positive": best_candidate.get("wf_positive_windows", 0),
                "verdict": best_candidate.get("verdict", "NO_EDGE")
            })
        else:
            summary.append({
                "frequency_band": label,
                "best_strategy": "NONE",
                "trades_per_day": 0.0,
                "profit_factor": 0.0,
                "net_expectancy": 0.0,
                "bootstrap_ci": "[0.0, 0.0]",
                "max_drawdown_pct": 0.0,
                "walk_forward_positive": 0,
                "verdict": "V37_NO_ROBUST_PROFITABLE_EDGE"
            })

    return summary
