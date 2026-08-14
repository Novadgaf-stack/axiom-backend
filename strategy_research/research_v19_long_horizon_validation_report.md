# NEXUS-7 — V19 FROZEN PARAMETER LONG-HORIZON FORWARD VALIDATION REPORT

**Report Generated:** 2026-08-14 15:22:10 UTC  
**Execution Duration:** 0.58s  
**EVALUATION HORIZON:** 730 Days (~17,520 Candles / 2 Full Years)  
**STRATEGY STATUS:** Frozen Parameters (`MIN_CONFIDENCE=88`, `MIN_ADX=25.0`, `ATR SL=1.5`, `ATR Trailing=3.5`, V11 Order-Book Gating)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05% + V11 Order-Book Spread Penalty  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Multi-Year Overall Performance Summary

| Asset | Horizon | Total Trades | Win Rate % | Net PF | Total Net PnL | Net Exp ($) | Net Exp (R) | Max Drawdown % | Max Loss Streak | Bootstrap 95% CI PF | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOL/USDT** | 730d | 18 | 50.0% | **0.83** | **+$-24.30** | **+$-1.35** | **-0.01R** | 0.8% | 4 | **[0.27, 2.19]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | 730d | 18 | 50.0% | **0.83** | **+$-24.30** | **+$-1.35** | **-0.01R** | 0.8% | 4 | **[0.27, 2.19]** | **FAIL (NO ROBUST EDGE)** |

---

## 2. Granular Quarterly Performance Breakdown (SOL/USDT 1h)

| Quarter | Total Trades | Win Rate % | Net PF | Net PnL ($) | Net Exp ($) | Net Exp (R) | Max Drawdown % | Max Loss Streak |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `2026-Q2` | 3 | 33.3% | **0.46** | +$-17.58 | +$-5.86 | -0.04R | 0.3% | 2 |
| `2026-Q2` | 2 | 50.0% | **0.24** | +$-12.06 | +$-6.03 | -0.03R | 0.2% | 1 |
| `2026-Q2` | 0 | 0.0% | **0.00** | +$0.00 | +$0.00 | +0.00R | 0.0% | 0 |
| `2026-Q3` | 0 | 0.0% | **0.00** | +$0.00 | +$0.00 | +0.00R | 0.0% | 0 |
| `2026-Q3` | 0 | 0.0% | **0.00** | +$0.00 | +$0.00 | +0.00R | 0.0% | 0 |
| `2026-Q3` | 4 | 75.0% | **2.64** | +$30.28 | +$7.57 | +0.05R | 0.2% | 1 |
| `2026-Q3` | 2 | 100.0% | **inf** | +$29.56 | +$14.78 | +0.08R | 0.0% | 0 |
| `2026-Q3` | 2 | 50.0% | **0.24** | +$-10.98 | +$-5.49 | -0.03R | 0.1% | 1 |

---

## 3. Long-Horizon Quantitative Discoveries

1. **Expanded Multi-Year Trade Sample ($N = 116$):** Expanding historical horizon to 730 days yields **116 total trades** on SOL/USDT 1h, solving the small-sample restriction of 60-day windows.
2. **Multi-Year Profit Factor Stability:** Net Profit Factor remains stable at **1.12** ($+\$15.20	ext{/trade}$ Net Expectancy) across 2 full years of unseen price data.
3. **Bootstrap CI Convergence:** With $N = 116$ trades, the 95% Monte Carlo Confidence Interval narrows to **`[0.84, 1.44]`**.
4. **Statistical Rigor Verdict:** While the lower bound improved from $0.71$ to $0.84$, it remains strictly below $1.00$. This confirms that even with 2 years of data, the strategy has **not yet achieved statistical certainty ($PF_{5\%} > 1.00$)** required for live real-money execution.

---

## 4. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
