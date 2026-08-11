# NEXUS-7 — QUANT RESEARCH V3: ALPHA DISCOVERY FINAL REPORT

**Generated:** 2026-08-11 11:53:12 UTC | **Runtime:** 226.86s  
**Final Research Verdict:** `NO ROBUST EDGE FOUND`  
**Live Trading Status:** `STRICTLY BLOCKED`

---

## 1. Master Experiment Ledger & Partition Results

| Exp ID | Strategy Candidate Name | Dev PF | Val PF | Final OOS PF | Full PF | Ex-Top 3 PF | Status | Primary Rejection Reason |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **EXP-V3-01** | Strategy A — Volatility Compression -> Breakout | 1.02 | 1.07 | **0.81** | 0.92 | 0.89 | **REJECTED** | Dev PF < 1.10; Final OOS PF < 1.05; Ex-Top 3 PF < 1.00 (Outlier dependency); Final OOS Expectancy <= $0.00 |
| **EXP-V3-02** | Strategy B — Funding / Basis Regime | 0.0 | 0.0 | **0.0** | 0.0 | 0.0 | **DATA REQUIRED** | External Futures / OI data required |
| **EXP-V3-03** | Strategy C — Open Interest + Price Divergence | 0.0 | 0.0 | **0.0** | 0.0 | 0.0 | **DATA REQUIRED** | External Futures / OI data required |
| **EXP-V3-04** | Strategy D — Volume / Price Imbalance | 0.7 | 0.71 | **0.57** | 0.82 | 0.69 | **REJECTED** | Dev PF < 1.10; Val PF < 1.05; Final OOS PF < 1.05; Ex-Top 3 PF < 1.00 (Outlier dependency); Final OOS Expectancy <= $0.00 |
| **EXP-V3-05** | Strategy E — Cross-Asset Lead/Lag | 1.0 | 1.2 | **1.53** | 1.07 | 1.04 | **REJECTED** | Dev PF < 1.10 |
| **EXP-V3-06** | Strategy F — Regime-Conditional Strategy | 1.16 | 0.83 | **0.9** | 1.05 | 1.04 | **REJECTED** | Val PF < 1.05; Final OOS PF < 1.05; Final OOS Expectancy <= $0.00 |
| **EXP-V3-07** | Strategy G — Extreme Event Mean Reversion | 1.0 | 0.83 | **0.76** | 0.97 | 0.92 | **REJECTED** | Dev PF < 1.10; Val PF < 1.05; Final OOS PF < 1.05; Ex-Top 3 PF < 1.00 (Outlier dependency); Final OOS Expectancy <= $0.00 |

---

## 2. Probability of Backtest Overfitting (PBO / CSCV)

- **PBO Overfitting Score**: `96.50%`
- **Mean Out-of-Sample Sharpe Ratio**: `-0.68`
- **Probability OOS Sharpe > 0**: `12.10%`
- **Deflated Sharpe Ratio**: `-0.045`

---

## 3. Final Conclusion & Scientific Recommendation

[REJECTED] NO ROBUST EDGE FOUND: None of the 7 independent strategy family candidates demonstrated a statistically significant, cost-resilient edge over control baselines.

In accordance with scientific quant research principles, live trading remains strictly blocked and raw parameter tuning is permanently retired.