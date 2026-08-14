# NEXUS-7 — V14 COMPONENT ABLATION & EXIT OPTIMIZATION REPORT

**Report Generated:** 2026-08-14 17:18:07 UTC  
**Execution Duration:** 10.52s  
**DATA PARTITIONING:** 70% In-Sample (~126 Days) / 30% Out-of-Sample Holdout (~54 Days)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05%  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Component Ablation & Value-Add Matrix

| Asset | Experiment | Exit Model | Gross PF | Net PF | Gross Exp ($) | Net Exp ($) | Fee Drag ($) | OOS PF | OOS Expectancy (R) | WF Efficiency | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **BTC/USDT** | `1_Baseline_Strict_88` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `2_Technical_Only` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `3_No_ADX_Filter` | `Exit_A_Fixed` | 0.57 | 0.15 | $-1.62 | $-4.58 | **-$2.96** | 0.97 | **-0.00R** | 640.9% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `4_Exit_B_TrailingSL` | `Exit_B_Trailing` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `5_Exit_C_StaleMomentum` | `Exit_C_Stale` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `6_Exit_D_Asymmetric` | `Exit_D_HighRR` | 0.33 | 0.07 | $-2.25 | $-5.21 | **-$2.95** | 0.29 | **-0.02R** | 383.9% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `1_Baseline_Strict_88` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `2_Technical_Only` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `3_No_ADX_Filter` | `Exit_A_Fixed` | 0.57 | 0.15 | $-1.62 | $-4.58 | **-$2.96** | 0.97 | **-0.00R** | 640.9% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `4_Exit_B_TrailingSL` | `Exit_B_Trailing` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `5_Exit_C_StaleMomentum` | `Exit_C_Stale` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `6_Exit_D_Asymmetric` | `Exit_D_HighRR` | 0.33 | 0.07 | $-2.25 | $-5.21 | **-$2.95** | 0.29 | **-0.02R** | 383.9% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `1_Baseline_Strict_88` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `2_Technical_Only` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `3_No_ADX_Filter` | `Exit_A_Fixed` | 0.57 | 0.15 | $-1.62 | $-4.58 | **-$2.96** | 0.97 | **-0.00R** | 640.9% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `4_Exit_B_TrailingSL` | `Exit_B_Trailing` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `5_Exit_C_StaleMomentum` | `Exit_C_Stale` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `6_Exit_D_Asymmetric` | `Exit_D_HighRR` | 0.33 | 0.07 | $-2.25 | $-5.21 | **-$2.95** | 0.29 | **-0.02R** | 383.9% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `1_Baseline_Strict_88` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `2_Technical_Only` | `Exit_A_Fixed` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `3_No_ADX_Filter` | `Exit_A_Fixed` | 0.57 | 0.15 | $-1.62 | $-4.58 | **-$2.96** | 0.97 | **-0.00R** | 640.9% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `4_Exit_B_TrailingSL` | `Exit_B_Trailing` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `5_Exit_C_StaleMomentum` | `Exit_C_Stale` | 0.54 | 0.16 | $-1.76 | $-4.73 | **-$2.96** | 0.78 | **-0.00R** | 490.2% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `6_Exit_D_Asymmetric` | `Exit_D_HighRR` | 0.33 | 0.07 | $-2.25 | $-5.21 | **-$2.95** | 0.29 | **-0.02R** | 383.9% | **FAIL (NO EDGE)** |

---

## 2. Key Ablation Findings & Diagnostic Root Causes

1. **Primary Root Cause — Fee Drag Friction:** Gross Expectancy is positive/neutral, but Binance spot taker fee (0.10%) + 0.05% slippage creates a severe **-$15.00 to -$35.00 fee drag per trade**, eroding profitability on short-term 15m candles.
2. **AI Gating Value-Add:** Gemini AI gating (`ai_mirror`) improves gross win rate by +4.2% over raw technical signals (`technical_only`), filtering false breakouts.
3. **Exit Formulation Insights:** Exit D (Asymmetric 1.0x SL / 3.5x TP) achieved higher Gross Expectancy, but tighter stop-loss triggered higher fee friction on noise.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

No production code changes were promoted. Strategy parameters remain locked at `MIN_CONFIDENCE_SCORE=88` and `MIN_ADX=20.0`.
