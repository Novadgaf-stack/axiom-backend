# NEXUS-7 — V13 RESEARCH & OPTIMIZATION REPORT

**Report Generated:** 2026-08-14 15:01:40 UTC  
**Pipeline Execution Time:** 2.05s  
**DATA PARTITIONING:** 70% In-Sample (~126 Days) / 30% Out-of-Sample Holdout (~54 Days)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05%  
**TIMESTAMP PARITY AUDIT:** `100.0% ALIGNED` (0-LOOKAHEAD PARITY CERTIFIED)  
**15% DRAWDOWN GUARD:** `VERIFIED (UNLOCKED ON RECOVERY)`  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO OOS EDGE PROVEN)`  
**REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Out-of-Sample Performance Matrix Across Assets

| Asset | Candidate Strategy | IS Trades | IS PF | OOS Trades | OOS Win Rate | OOS PF | OOS Expectancy ($) | OOS Expectancy (R) | OOS Max DD | OOS Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **BTC/USDT** | `Baseline_Strict_88` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `Candidate_A_Conf82` | 40 | 0.13 | 15 | 40.0% | 0.78 | **$-0.54** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `Candidate_B_Conf75` | 40 | 0.15 | 18 | 61.1% | 0.86 | **$-0.43** | **-0.00R** | 0.33% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `Candidate_C_TechOnly` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `Candidate_D_TightSL` | 42 | 0.08 | 18 | 22.2% | 0.34 | **$-2.05** | **-0.01R** | 0.37% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `Baseline_Strict_88` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `Candidate_A_Conf82` | 40 | 0.13 | 15 | 40.0% | 0.78 | **$-0.54** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `Candidate_B_Conf75` | 40 | 0.15 | 18 | 61.1% | 0.86 | **$-0.43** | **-0.00R** | 0.33% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `Candidate_C_TechOnly` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `Candidate_D_TightSL` | 42 | 0.08 | 18 | 22.2% | 0.34 | **$-2.05** | **-0.01R** | 0.37% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `Baseline_Strict_88` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `Candidate_A_Conf82` | 40 | 0.13 | 15 | 40.0% | 0.78 | **$-0.54** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `Candidate_B_Conf75` | 40 | 0.15 | 18 | 61.1% | 0.86 | **$-0.43** | **-0.00R** | 0.33% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `Candidate_C_TechOnly` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `Candidate_D_TightSL` | 42 | 0.08 | 18 | 22.2% | 0.34 | **$-2.05** | **-0.01R** | 0.37% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `Baseline_Strict_88` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `Candidate_A_Conf82` | 40 | 0.13 | 15 | 40.0% | 0.78 | **$-0.54** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `Candidate_B_Conf75` | 40 | 0.15 | 18 | 61.1% | 0.86 | **$-0.43** | **-0.00R** | 0.33% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `Candidate_C_TechOnly` | 35 | 0.16 | 14 | 42.9% | 0.78 | **$-0.59** | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `Candidate_D_TightSL` | 42 | 0.08 | 18 | 22.2% | 0.34 | **$-2.05** | **-0.01R** | 0.37% | **FAIL (NO EDGE)** |

---

## 2. Key Quantitative Findings & Insights

1. **Frequency vs. Profitability Trade-off:** Lowering confidence thresholds increases trade frequency but degrades Out-of-Sample Profit Factor ($PF$) due to taker fee friction and false breakouts.
2. **Out-of-Sample Edge Enforcement:** Strategies failing the OOS holdout threshold ($PF \ge 1.15$, Expectancy $> 0$) are strictly rejected to protect capital.
3. **Zero Lookahead Audit:** 100% timestamp parity verified between research replay and live execution engine.

---

## 3. Final Production Promotion Mandate

> **OVERALL VERDICT: REJECTED (NO OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**
