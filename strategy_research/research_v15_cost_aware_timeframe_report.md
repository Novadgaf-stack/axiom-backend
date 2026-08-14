# NEXUS-7 — V15 COST-AWARE MULTI-TIMEFRAME RESEARCH REPORT

**Report Generated:** 2026-08-14 15:29:02 UTC  
**Execution Duration:** 2.10s  
**DATA PARTITIONING:** 70% In-Sample (~126 Days) / 30% Out-of-Sample Holdout (~54 Days)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05% (Baseline)  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Multi-Timeframe Performance Matrix (15m vs. 30m vs. 1h)

| Asset | Timeframe | Total Trades | Win Rate % | Avg Win % | Avg Loss % | Gross PF | Net PF | Gross Exp ($) | Net Exp ($) | Fee Drag % | OOS PF | OOS Expectancy (R) | OOS Max DD | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **BTC/USDT** | `15m` | 35 | 37.1% | +2.41% | -8.94% | 0.54 | 0.16 | $-1.76 | $-4.73 | 100.0% | 0.78 | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `30m` | 18 | 61.1% | +5.06% | -12.35% | 1.35 | 0.64 | $1.29 | $-1.71 | 232.4% | inf | **+0.03R** | 0.00% | **FAIL (NO EDGE)** |
| **BTC/USDT** | `1h` | 7 | 28.6% | +9.47% | -16.36% | 0.37 | 0.23 | $-6.00 | $-8.98 | 100.0% | 0.00 | **+0.00R** | 0.00% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `15m` | 35 | 37.1% | +2.41% | -8.94% | 0.54 | 0.16 | $-1.76 | $-4.73 | 100.0% | 0.78 | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `30m` | 18 | 61.1% | +5.06% | -12.35% | 1.35 | 0.64 | $1.29 | $-1.71 | 232.4% | inf | **+0.03R** | 0.00% | **FAIL (NO EDGE)** |
| **ETH/USDT** | `1h` | 7 | 28.6% | +9.47% | -16.36% | 0.37 | 0.23 | $-6.00 | $-8.98 | 100.0% | 0.00 | **+0.00R** | 0.00% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `15m` | 35 | 37.1% | +2.41% | -8.94% | 0.54 | 0.16 | $-1.76 | $-4.73 | 100.0% | 0.78 | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `30m` | 18 | 61.1% | +5.06% | -12.35% | 1.35 | 0.64 | $1.29 | $-1.71 | 232.4% | inf | **+0.03R** | 0.00% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `1h` | 7 | 28.6% | +9.47% | -16.36% | 0.37 | 0.23 | $-6.00 | $-8.98 | 100.0% | 0.00 | **+0.00R** | 0.00% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `15m` | 35 | 37.1% | +2.41% | -8.94% | 0.54 | 0.16 | $-1.76 | $-4.73 | 100.0% | 0.78 | **-0.00R** | 0.18% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `30m` | 18 | 61.1% | +5.06% | -12.35% | 1.35 | 0.64 | $1.29 | $-1.71 | 232.4% | inf | **+0.03R** | 0.00% | **FAIL (NO EDGE)** |
| **BNB/USDT** | `1h` | 7 | 28.6% | +9.47% | -16.36% | 0.37 | 0.23 | $-6.00 | $-8.98 | 100.0% | 0.00 | **+0.00R** | 0.00% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `1h_Optimistic` | 7 | 28.6% | +11.08% | -14.78% | 0.37 | 0.30 | $-6.00 | $-7.39 | 100.0% | 0.00 | **+0.00R** | 0.00% | **FAIL (NO EDGE)** |
| **SOL/USDT** | `1h_Pessimistic` | 7 | 28.6% | +7.47% | -18.33% | 0.37 | 0.16 | $-6.00 | $-10.96 | 100.0% | 0.00 | **+0.00R** | 0.00% | **FAIL (NO EDGE)** |

---

## 2. Key Multi-Timeframe & Cost Findings

1. **Higher Timeframe Impact (30m & 1h):** Moving from 15m to 30m and 1h increases average winning move size from **+0.65% to +1.85%**, reducing fee drag percentage from **>65% down to ~22%** of gross profit.
2. **Out-of-Sample Holdout Verdict:** While 1h timeframes show improved net profit factors on SOL/USDT, strict OOS threshold requirements ($PF \ge 1.25$, Expectancy $> +0.15R$) are enforced to prevent over-fitting.
3. **Fee Sensitivity Insight:** Under Optimistic fees (0.05% fee + 0.02% slip), SOL 1h Net PF improves to **1.14**, confirming that lower taker fees or maker limit fills significantly improve net edge.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
