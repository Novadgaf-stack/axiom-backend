"""
NEXUS-7 — RESEARCH V11 ORDER BOOK FEATURE TRANSFORMER & LEAKAGE AUDITOR
1. Transforms raw tick stream and L2 depth into 4 active mathematical strategy features.
2. Audits 0% data leakage into the 3,000-bar locked holdout window.
3. Connects order-book features directly into app/strategy_engine.py.
4. Exports research_v11_true_order_book_alpha_report.md.
"""
