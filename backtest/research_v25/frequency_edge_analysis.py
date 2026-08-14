"""
NEXUS-7 — RESEARCH V25 FREQUENCY EDGE ANALYSIS MODULE
Constructs the Frequency vs Profitability Frontier Curve across trade frequency steps.
"""
from typing import List, Dict, Any

def build_frontier_curve(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    frontier = []
    for r in results:
        m = r["metrics_015"]
        frontier.append({
            "candidate": r["candidate_name"],
            "trades_per_day": m["avg_trades_per_day"],
            "net_pf": m["net_pf"],
            "net_exp_r": m["net_exp_r"],
            "max_dd_pct": m["max_dd_pct"],
            "ci_lower": m["ci_lower"],
            "verdict": r["verdict"]
        })
    return frontier
