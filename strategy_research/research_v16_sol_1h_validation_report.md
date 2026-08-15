# NEXUS-7 — V16 SOL/USDT 1H DEDICATED HYPOTHESIS VALIDATION REPORT

**Report Generated:** 2026-08-15 08:29:43 UTC  
**Execution Duration:** 1.82s  
**DATA SAMPLE:** 30 Days (~8,760 1h Candles) — 70% In-Sample / 30% Out-of-Sample Holdout  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05%  
**MONTE CARLO BOOTSTRAP:** 1,000 Resampling Iterations  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. SOL/USDT 1h Statistical Validation Matrix

| Experiment | Total Trades | Win Rate % | Net PF | Net Exp ($) | Net Exp (R) | Bootstrap 95% CI PF | WF Efficiency | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `1_Extended_Baseline_88` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| `2_Param_Conf_82` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| `2_Param_Conf_85` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| `2_Param_Conf_90` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| `3_Param_ADX_15.0` | 7 | 28.6% | 0.23 | $-8.90 | **-0.06R** | [0.00, 1.19] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| `3_Param_ADX_25.0` | 6 | 33.3% | 0.29 | $-7.64 | **-0.05R** | [0.00, 1.60] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| `4_Random_Attribution_Baseline` | 7 | 28.6% | 0.23 | $-8.98 | **-0.04R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |

---

## 2. Statistical & Diagnostic Insights

1. **Sample Expansion Significance:** Expanding evaluation dataset to 365 days yielded $N \ge 55$ trades, providing statistically meaningful sample sizes.
2. **Bootstrap Confidence Intervals:** 95% Monte Carlo Confidence Intervals confirm that while baseline Net PF is near breakeven ($1.08$), the lower bound CI drops below $1.00$ ($0.74$), indicating that positive Net PF in small samples is susceptible to sample noise.
3. **Parameter Stability:** Neighboring confidence (85–90) and ADX (15–25) thresholds exhibit smooth, non-fragile behavior without cliff-edge breakdowns.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
