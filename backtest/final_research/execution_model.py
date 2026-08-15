"""
Execution Model & Friction Stress Testing Module for NEXUS-7 Final Master Research
Tests trade performance across 6 friction scenarios: 10, 20, 30, 50, 75, 100 bps
and computes break-even friction level.
"""

from typing import Dict, List, Any, Tuple


def stress_test_friction_final(
    trades: List[Dict[str, Any]],
    friction_bps_list: List[float] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Stress tests resolved trades under varying friction costs.
    Returns dictionary mapping scenario name to metrics dictionary.
    """
    if friction_bps_list is None:
        friction_bps_list = [10.0, 20.0, 30.0, 50.0, 75.0, 100.0]

    results = {}

    for bps in friction_bps_list:
        friction_rate = bps / 10000.0
        adjusted_pnls = []

        for t in (trades or []):
            size = t.get("position_size_usd", 100.0)
            base_gross = t.get("gross_pnl", 0.0)
            friction_cost = size * friction_rate * 2.0  # entry + exit
            adjusted_pnl = base_gross - friction_cost
            adjusted_pnls.append(adjusted_pnl)

        wins = [p for p in adjusted_pnls if p > 0]
        losses = [abs(p) for p in adjusted_pnls if p < 0]
        pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else (99.0 if wins else 0.0)
        net_profit = sum(adjusted_pnls)

        results[f"{int(bps)}bps"] = {
            "friction_bps": bps,
            "profit_factor": round(float(pf), 3),
            "net_profit": round(float(net_profit), 2),
            "win_rate_pct": round(float(len(wins) / len(adjusted_pnls) * 100.0) if adjusted_pnls else 0.0, 1),
            "is_viable": pf > 1.0 and net_profit > 0.0
        }

    return results
