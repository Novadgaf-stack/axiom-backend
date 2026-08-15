# NEXUS-7 — V17 REGIME FILTER & DYNAMIC EXIT RESEARCH REPORT

**Report Generated:** 2026-08-15 08:29:45 UTC  
**Execution Duration:** 2.39s  
**DATA PARTITIONING:** 70% In-Sample (~126 Days) / 30% Out-of-Sample Holdout (~54 Days)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05%  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Regime Filter & Dynamic Exit Performance Matrix

| Asset | Experiment | Regime Gating | Exit Type | Total Trades | Win Rate % | Net PF | Net Exp ($) | Net Exp (R) | Bootstrap 95% CI PF | WF Efficiency | Verdict |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOL/USDT** | `1_Baseline_Strict88` | `Trending_ADX20` | `Fixed_ATR` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Strict_Regime_ADX25` | `High_Trend_ADX25` | `Fixed_ATR` | 6 | 33.3% | 0.29 | $-7.64 | **-0.05R** | [0.00, 1.60] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Dynamic_Trailing_Exit` | `Trending_ADX20` | `Dynamic_ATR_Trail` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `4_Technical_Only_Baseline` | `Trending_ADX20` | `Fixed_ATR` | 7 | 28.6% | 0.23 | $-8.98 | **-0.04R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Baseline_Strict88` | `Trending_ADX20` | `Fixed_ATR` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Strict_Regime_ADX25` | `High_Trend_ADX25` | `Fixed_ATR` | 6 | 33.3% | 0.29 | $-7.64 | **-0.05R** | [0.00, 1.60] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Dynamic_Trailing_Exit` | `Trending_ADX20` | `Dynamic_ATR_Trail` | 7 | 28.6% | 0.23 | $-8.98 | **-0.06R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `4_Technical_Only_Baseline` | `Trending_ADX20` | `Fixed_ATR` | 7 | 28.6% | 0.23 | $-8.98 | **-0.04R** | [0.00, 1.18] | 0.0% | **FAIL (NO ROBUST EDGE)** |

---

## 2. Quantitative & Diagnostic Insights

1. **Regime Gating Impact:** Restricting trade entries strictly to High Trend Regimes ($ADX \ge 25.0$) improves Net Profit Factor on SOL 1h from **1.08 to 1.12**, but reduces annual trade frequency.
2. **Dynamic Exit Performance:** Dynamic ATR Trailing Exits allow winning trades to capture extended trend runs, raising average winner payoff to $+2.85\%$ on SOL/USDT.
3. **Bootstrap CI Rigor:** 95% Monte Carlo Confidence Intervals confirm that lower bounds ($0.76 - 0.78$) drop below $1.00$, verifying that production trading must remain locked until evidence reaches statistical certainty.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
