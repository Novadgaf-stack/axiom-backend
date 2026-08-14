"""
NEXUS-7 — RESEARCH V25 STRATEGY EXPANSION MODULE
Evaluates 6 strategy families: Trend Continuation, Pullback, Breakout, Momentum, Mean Reversion, Volatility Expansion.
"""
from typing import List, Dict, Any

STRATEGY_FAMILIES = [
    "TrendContinuation",
    "Pullback",
    "Breakout",
    "Momentum",
    "MeanReversion",
    "VolatilityExpansion"
]

def list_strategy_families() -> List[str]:
    return STRATEGY_FAMILIES
