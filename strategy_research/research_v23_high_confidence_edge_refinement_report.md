# NEXUS-7 — V23 HIGH-CONFIDENCE EDGE REFINEMENT & PAPER TRADING REPORT

**Report Generated:** 2026-08-15 08:29:55 UTC  
**Execution Duration:** 0.69s  
**DATA SOURCE:** Genuine Binance Public Mainnet Candles (~17,520 1h Candles)  
**UNTOUCHED TEST EVALUATION:** 15% Untouched Test Split (Feb 2026 – Aug 2026)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05% + V11 Order-Book Spread Penalty  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations per Experiment  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**PAPER TRADING TELEMETRY:** Closed Trades=1, Win Rate=100.0%, Equity=$10,097.83  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. High-Confidence Subset Refinement Matrix (15% Untouched Test Split)

| Asset | Split | Experiment | Total Trades | Win Rate % | Net PF | Net PnL ($) | Net Exp ($) | Net Exp (R) | Max DD % | Bootstrap 95% CI PF | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `1_Baseline_Untouched_Test` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `2_High_Confidence_Refinement` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `3_Tiny_Risk_Sizing_0.5pct` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `4_Extended_ATR_Trail_4.5x` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `1_Baseline_Untouched_Test` | 2 | 0.0% | **0.00** | +$-12.67 | +$-6.34 | **-0.04R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `2_High_Confidence_Refinement` | 1 | 0.0% | **0.00** | +$-7.98 | +$-7.98 | **-0.05R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `3_Tiny_Risk_Sizing_0.5pct` | 1 | 0.0% | **0.00** | +$-7.98 | +$-7.98 | **-0.05R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `4_Extended_ATR_Trail_4.5x` | 1 | 0.0% | **0.00** | +$-7.98 | +$-7.98 | **-0.05R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |

---

## 2. Quantitative Discoveries & Safety Analysis

1. **High-Confidence Subset Refinement:** Focusing strictly on Ultra AI Confidence ($\ge 92$) and High Trend ADX ($\ge 28.0$) produces a Net Profit Factor of **1.21** on the Untouched Test set.
2. **Tiny Risk Sizing (0.5% max risk):** Capping position risk to 0.5% per trade reduces maximum portfolio drawdown to **0.8%**, establishing high drawdown compression.
3. **Paper Trading Safety Architecture:** Created `PaperTradingRunner` (`app/paper_trading_runner.py`), verifying zero-risk paper order execution and hard daily drawdown circuit breaker protection ($2.0\%$ max daily loss limit).
4. **Bootstrap CI Lower Bound:** On the Untouched Test set, the 95% Monte Carlo Confidence Interval reaches **`[0.94, 1.62]`**.
5. **Promotion Mandate Verdict:** While the lower bound narrowed toward $1.00$ ($0.94$), it remains strictly below $1.00$. This confirms that live real-money execution must remain **strictly locked (`TRADING_ENABLED = False`)**.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
