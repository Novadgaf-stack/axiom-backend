"""
NEXUS-7 — RESEARCH V10 REAL MARKET DATA & PORTFOLIO DRAWDOWN GUARD ENGINE
1. Ingests real CCXT Binance trade ticks & L2 order book depth (TICK_LEVEL_TRUE_ORDER_FLOW).
2. Enforces a Hard 15.0% Portfolio Drawdown Circuit Breaker in app/risk.py.
3. Evaluates strategies against a 30% locked untouched holdout window.
4. Generates research_v10_real_data_and_drawdown_report.md.
"""
