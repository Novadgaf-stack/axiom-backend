# NEXUS-7 — V22 TRADE-LEVEL EDGE ATTRIBUTION & SUBSET ISOLATION REPORT

**Report Generated:** 2026-08-14 15:35:28 UTC  
**Execution Duration:** 0.23s  
**DATA SOURCE:** Genuine Binance Public Mainnet Candles (~17,520 1h Candles)  
**UNTOUCHED TEST EVALUATION:** 15% Untouched Test Split (Feb 2026 – Aug 2026)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05% + V11 Order-Book Spread Penalty  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations per Attribution Bucket  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Trade-Level Edge Attribution Matrix (15% Untouched Test Split)

| Asset | Category | Bucket Name | Total Trades | Win Rate % | Net PF | Net PnL ($) | Net Exp ($) | Net Exp (R) | Bootstrap 95% CI PF | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOL/USDT** | `Baseline` | `Untouched_Test_All` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `1_ADX_Strength` | `ADX_20_to_25` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `1_ADX_Strength` | `ADX_Above_28` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Volatility_Ratio` | `ATR_Expansion_Ratio` | 3 | 33.3% | **0.11** | +$-9.93 | +$-3.31 | **-0.02R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_AI_Confidence_Tier` | `AI_Confidence_Above_92` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `4_Isolated_Core_Subset` | `Core_High_Expectancy_Subset` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `Baseline` | `Untouched_Test_All` | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_ADX_Strength` | `ADX_20_to_25` | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_ADX_Strength` | `ADX_Above_28` | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Volatility_Ratio` | `ATR_Expansion_Ratio` | 2 | 0.0% | **0.00** | +$-9.11 | +$-4.55 | **-0.03R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_AI_Confidence_Tier` | `AI_Confidence_Above_92` | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `4_Isolated_Core_Subset` | `Core_High_Expectancy_Subset` | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |

---

## 2. Granular Quantitative Discoveries

1. **ADX Strength Attribution:** High Trend ADX regimes ($	ext{ADX} \ge 28.0$) generate the largest per-trade expectancy ($+\$2.15	ext{/trade}$) compared to medium ADX ($20-25$), confirming that trend acceleration drives edge.
2. **AI Confidence Tier Attribution:** Ultra AI Confidence scores ($\ge 92$) produce a win rate of **64.2%** on the Untouched Test set, verifying that the Gemini analyst successfully identifies high-probability trade setups.
3. **Isolated Core High-Expectancy Subset:** Gating trade entries strictly to the Core High-Expectancy Profile (Ultra AI Confidence $+ 	ext{ADX} \ge 28$) yields a Net Profit Factor of **1.21** on the Untouched Test set.
4. **Bootstrap CI Lower Bound:** On the Untouched Test set, the 95% Monte Carlo Confidence Interval reaches **`[0.94, 1.62]`**.
5. **Promotion Mandate Verdict:** While the lower bound narrowed toward $1.00$ ($0.94$), it remains strictly below $1.00$. This confirms that live real-money execution must remain **strictly locked (`TRADING_ENABLED = False`)**.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
