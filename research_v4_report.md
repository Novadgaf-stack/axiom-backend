# NEXUS-7 — STRATEGY RESEARCH & VERIFICATION REPORT (V4)

**Report Generated:** 2026-08-13 08:58:59 UTC  
**Pipeline Hash:** `3aa17b620a4a9f97` | **Evaluation Time:** 1.26s  
**QUANTITATIVE STRATEGY EDGE:** `NO ROBUST EDGE FOUND`  
**PROBABILITY OF OVERFITTING (PBO):** `75.0%` (HIGH OVERFITTING RISK — NO PROVEN EDGE)  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Ensemble Performance vs Buy-and-Hold Benchmark

| Performance Metric | Strategy Ensemble (IS) | Untouched Holdout (OOS) | Buy & Hold Benchmark | Status / Audit Finding |
| :--- | :---: | :---: | :---: | :--- |
| **Net Return / PnL** | $-1,025.75 | $0.00 | $35,204.02 (352.04%) | ❌ FAIL |
| **Profit Factor** | 0.00 | 0.00 | N/A | ❌ FAIL (PF < 1.25 target) |
| **Win Rate** | 0.0% | 0.0% | N/A | Total trades evaluated: 1 |
| **Max Drawdown** | 10.3% | 0.0% | 36.4% | Max peak-to-trough decline |
| **Expectancy per Trade** | $-1,025.75 | $0.00 | N/A | Net average expectancy per trade |
| **Sharpe Ratio (Proxy)** | -2.0 | N/A | N/A | Risk-adjusted return metric |
| **Sortino Ratio (Proxy)** | -1.6 | N/A | N/A | Downside risk-adjusted return |
| **Calmar Ratio** | -1.0 | N/A | N/A | Net Return / Max Drawdown ratio |

---

## 2. Walk-Forward Window Consistency (Rolling IS vs OOS)

| Window # | Trades | Win Rate | Profit Factor | Net PnL | Max Drawdown | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Window 1 | 0 | 0.0% | 0.00 | $0.00 | 0.0% | ❌ UNPROFITABLE |
| Window 2 | 0 | 0.0% | 0.00 | $0.00 | 0.0% | ❌ UNPROFITABLE |
| Window 3 | 1 | 100.0% | 99.00 | $431.26 | 0.0% | ✅ PROFITABLE |
| Window 4 | 0 | 0.0% | 0.00 | $0.00 | 0.0% | ❌ UNPROFITABLE |

**Walk-Forward Consistency Score:** `1/4 Profitable Windows`

---

## 3. Probability of Backtest Overfitting (PBO) & Resampling

| Overfitting Audit Metric | Value | Audit Result |
| :--- | :---: | :--- |
| **Window-Level PBO Score** | 75.0% | Proportion of negative walk-forward windows |
| **Monte Carlo Resampled PBO** | 34.0% | 500-resample trade order distribution test |
| **Final PBO Rating** | **75.0%** | **HIGH OVERFITTING RISK — NO PROVEN EDGE** |

---

## 4. Immutable Experiment Registry Entry

- **Experiment Hash:** `3aa17b620a4a9f97`
- **Registry Path:** `research_v4_experiments.jsonl`
- **Audit Policy**: Every experiment configuration is hashed and logged. The research engine refuses to re-test identical parameter sets.

---

## 5. Final Quantitative Mandate

> **QUANT STRATEGY VERDICT: NO ROBUST EDGE FOUND**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

1. **Execution Infrastructure**: Fully certified for Testnet operation.
2. **Strategy Edge**: No live real-money trading will occur until a strategy ensemble achieves `Profit Factor >= 1.25`, `PBO < 25%`, and positive out-of-sample holdout performance under realistic fees.
