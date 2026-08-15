"""
Expectancy Frontier Module for NEXUS-7 Final Master Research
Constructs the Frequency Frontier table across 7 target frequency bands:
<0.25, 0.25–0.50, 0.50–1.00, 1.00–1.50, 1.50–2.00, 2.00–3.00, 3.00+ trades/day.
Identifies the highest frequency region that retains genuine statistical evidence after costs.
"""

from typing import Dict, List, Any


FREQUENCY_BANDS_FINAL = [
    "LESS_THAN_0.25_TRADES_DAY",
    "0.25_TO_0.50_TRADES_DAY",
    "0.50_TO_1.00_TRADES_DAY",
    "1.00_TO_1.50_TRADES_DAY",
    "1.50_TO_2.00_TRADES_DAY",
    "2.00_TO_3.00_TRADES_DAY",
    "3.00_PLUS_TRADES_DAY"
]


def build_expectancy_frequency_frontier_final(
    strategy_results: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Groups candidate strategies into frequency bands and finds the highest-quality achievable frequency.
    """
    frontier = {}
    for band in FREQUENCY_BANDS_FINAL:
        frontier[band] = {
            "frequency_band": band,
            "best_strategy": "NONE",
            "trades_per_day": 0.0,
            "profit_factor": 0.0,
            "net_expectancy_usd": 0.0,
            "max_drawdown_pct": 0.0,
            "verdict": "NO_DEFENDED_EDGE"
        }

    for res in strategy_results:
        t_pd = res.get("trades_per_day", 0.0)
        pf = res.get("profit_factor", 0.0)

        if t_pd < 0.25:
            band = "LESS_THAN_0.25_TRADES_DAY"
        elif t_pd < 0.50:
            band = "0.25_TO_0.50_TRADES_DAY"
        elif t_pd < 1.00:
            band = "0.50_TO_1.00_TRADES_DAY"
        elif t_pd < 1.50:
            band = "1.00_TO_1.50_TRADES_DAY"
        elif t_pd < 2.00:
            band = "1.50_TO_2.00_TRADES_DAY"
        elif t_pd < 3.00:
            band = "2.00_TO_3.00_TRADES_DAY"
        else:
            band = "3.00_PLUS_TRADES_DAY"

        if pf > frontier[band]["profit_factor"]:
            frontier[band] = {
                "frequency_band": band,
                "best_strategy": res.get("strategy_name", "UNKNOWN"),
                "trades_per_day": round(float(t_pd), 2),
                "profit_factor": round(float(pf), 3),
                "net_expectancy_usd": round(float(res.get("net_expectancy_usd", 0.0)), 3),
                "max_drawdown_pct": round(float(res.get("max_drawdown_pct", 0.0)), 2),
                "verdict": res.get("verdict", "FRAGILE")
            }

    return frontier
