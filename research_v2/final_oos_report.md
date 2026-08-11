# NEXUS-7 — FINAL QUANTITATIVE RESEARCH REPORT (RESET V2)

**Generated:** 2026-08-11 11:33:02 UTC | **Runtime:** 109.19s  
**Final Research Verdict:** `NO ROBUST EDGE FOUND`  
**Live Trading Status:** `STRICTLY BLOCKED`

---

## 1. Master Experiment Ledger & Partition Leaderboard

| Exp ID | Strategy Candidate Name | Dev PF | Val PF | Final OOS PF | Full PF | Ex-Top 3 PF | Status | Primary Rejection Reason |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **EXP-V2-01** | Strategy A — Time-Series Momentum | 0.95 | 1.06 | **0.99** | 1.01 | 1.0 | **REJECTED** | Normal Maker PF < 1.10; Final OOS Expectancy <= $0.00 |
| **EXP-V2-02** | Strategy B — Cross-Sectional Relative Strength | 0.99 | 0.97 | **0.94** | 1.01 | 1.01 | **REJECTED** | Normal Maker PF < 1.10; Final OOS Expectancy <= $0.00 |
| **EXP-V2-03** | Strategy C — Volatility Breakout | 1.04 | 0.92 | **0.8** | 1.03 | 1.0 | **REJECTED** | Normal Maker PF < 1.10; Final OOS Expectancy <= $0.00 |
| **EXP-V2-04** | Strategy D — Statistical Z-Score Mean Reversion | 0.73 | 1.08 | **1.05** | 1.03 | 0.97 | **REJECTED** | Normal Maker PF < 1.10; Ex-Top 3 PF < 1.00 (Outlier dependency) |
| **EXP-V2-05** | Strategy E — Cross-Asset Lead/Lag Predictive Model | 0.85 | 1.11 | **1.0** | 0.96 | 0.93 | **REJECTED** | Normal Maker PF < 1.10; Ex-Top 3 PF < 1.00 (Outlier dependency) |
| **EXP-V2-06** | Strategy F — Market-Neutral Relative Value Spread | 0.95 | 0.87 | **0.89** | 0.97 | 0.96 | **REJECTED** | Normal Maker PF < 1.10; Ex-Top 3 PF < 1.00 (Outlier dependency); Final OOS Expectancy <= $0.00 |
| **EXP-V2-07** | Strategy G — Cost-Aware Expected Return Gate | 0.84 | 1.09 | **1.15** | 0.95 | 0.94 | **REJECTED** | Normal Maker PF < 1.10; Ex-Top 3 PF < 1.00 (Outlier dependency) |

---

## 2. Probability of Backtest Overfitting (PBO / CSCV)

- **PBO Overfitting Score**: `99.21%`

- **Mean Out-of-Sample Sharpe Ratio**: `-0.93`

- **Probability OOS Sharpe > 0**: `11.11%`

- **Deflated Sharpe Ratio**: `-0.007`


---

## 3. Final Conclusion & Scientific Recommendation

[REJECTED] NO ROBUST EDGE FOUND: None of the 7 independent strategy family candidates demonstrated a statistically significant, cost-resilient edge over control baselines.

In accordance with scientific quant research principles, live trading remains strictly blocked and raw parameter tuning is permanently retired.
