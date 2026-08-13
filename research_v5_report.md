# NEXUS-7 — ALPHA SELECTION & VERIFICATION REPORT (V5)

**Report Generated:** 2026-08-13 09:18:13 UTC  
**Pipeline Evaluation Duration:** 4.98s  
**PROMOTION GATE VERDICT:** `REJECTED (NO EDGE PROVEN)`  
**DEFLATED SHARPE RATIO (DSR):** `0.0%` (REJECTED (Sharpe <= 0))  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. 7-Stage Hard Promotion Gate Matrix

| Gate Stage | Requirement | Result | Audit Finding |
| :--- | :---: | :---: | :--- |
| **Stage 1: RESEARCH HYPOTHESIS** | **PASS** | ✅ PASS | Valid strategy structure and features defined |
| **Stage 2: IN-SAMPLE PERFORMANCE** | **FAIL** | ❌ FAIL | IS PF 0.00 (Target >= 1.25), Win Rate 0.0% |
| **Stage 3: WALK-FORWARD CONSISTENCY** | **FAIL** | ❌ FAIL | 25.0% Profitable Windows (Target >= 75%) |
| **Stage 4: PURGED OOS HOLDOUT** | **FAIL** | ❌ FAIL | OOS PnL $0.00, OOS PF 0.00 (Target >= 1.15) |
| **Stage 5: PBO / MULTIPLE-TESTING AUDIT** | **FAIL** | ❌ FAIL | PBO 75.0% (Target < 25%), DSR Prob 0.0% (Target >= 95%) |
| **Stage 6: FEE + SLIPPAGE STRESS** | **FAIL** | ❌ FAIL | Stress Expectancy $-100.93/trade under 0.10% fee + 0.05% slippage |
| **Stage 7: PROMOTION VERDICT** | **STRICTLY LOCKED** | ⚠️ STRICTLY LOCKED | LIVE REAL-MONEY TRADING REMAINS PERMANENTLY LOCKED |

---

## 2. Triple-Barrier Labeling Breakdown

| Barrier Event | Triggered Count | Percentage | Operational Meaning |
| :--- | :---: | :---: | :--- |
| **Upper Take-Profit Barrier (+2.0x ATR)** | 43 | 36.4% | Target profit level touched first |
| **Lower Stop-Loss Barrier (-1.0x ATR)** | 75 | 63.6% | Risk limit level touched first |
| **Max Hold Timeout (48 Bars)** | 0 | 0.0% | Closed at market after max holding period |

---

## 3. Ablation Study & Feature Sensitivity Breakdown (Canonical Trade Ledger)

| Component Step | Trades Evaluated | Win Rate | Expectancy / Trade | Net PnL | Profit Factor | Recommendation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline Consensus** | 1 | 0.0% | $-100.93 | $-100.93 | 0.00 | ✅ RETAIN |
| **+ Regime Filter** | 1 | 0.0% | $-100.93 | $-100.93 | 0.00 | ❌ DISCARD |
| **+ Volume Imbalance** | 0 | N/A | $0.00 | $0.00 | N/A | ✅ RETAIN |
| **+ MTF 4H Macro Bias** | 0 | N/A | $0.00 | $0.00 | N/A | ❌ DISCARD |
| **+ Volatility Squeeze** | 0 | N/A | $0.00 | $0.00 | N/A | ❌ DISCARD |

---

## 4. Control Baseline Benchmarking (6 Controls)

| Benchmark Baseline | Net PnL | Return % | Audit Comparison |
| :--- | :---: | :---: | :--- |
| **Buy & Hold Benchmark** | $35,204.02 | 352.04% | Passive buy & hold baseline |
| **No-Trade Control** | $0.00 | 0.0% | Zero activity baseline |
| **Simple Trend (EMA 20/50)** | $14,081.61 | 140.82% | Unfiltered technical trend following |
| **Simple Breakout (Donchian)** | $-3,520.40 | -35.2% | Unfiltered 20-period breakout |
| **Simple Mean Reversion** | $7,040.80 | 70.41% | Unfiltered mean reversion |
| **Random Entries Baseline** | $-750.92 | -7.51% | Monte Carlo random entry control |

---

## 5. Final Quantitative Mandate

> **PROMOTION GATE VERDICT: REJECTED (NO EDGE PROVEN)**  
> **QUANT STRATEGY EDGE: NO ROBUST EDGE FOUND**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

1. **Execution Infrastructure**: Operational infrastructure is certified for Testnet.
2. **Research Discipline**: The V5 Alpha Selection Framework correctly identified `NO ROBUST EDGE FOUND` and refused to falsely promote unproven strategies.
3. **Next Steps**: Continue multi-hypothesis feature research using Purged CV and Ablation testing before any live deployment consideration.
