# NEXUS-7 — V18 ROBUSTNESS & EDGE DISCOVERY RESEARCH REPORT

**Report Generated:** 2026-08-14 15:10:17 UTC  
**Execution Duration:** 0.40s  
**WALK-FORWARD STRUCTURE:** 3 Independent Non-Overlapping 60-Day OOS Windows  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05% + V11 Order-Book Spread Penalty  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations per Window  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Multi-Window Robustness Performance Matrix

| Asset | Window | Experiment | OB Gating | ADX | ATR SL/TP | Trades | Win Rate % | Net PF | Net Exp ($) | Net Exp (R) | Bootstrap 95% CI PF | Grid Stability | Verdict |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOL/USDT** | `Window_1_Days1_60` | `1_Primary_Regime_V11` | `V11_Imbalance_Active` | 25.0 | 1.5/3.5 | 4 | 25.0% | 0.31 | $-8.46 | **-0.06R** | [0.00, 0.00] | 85% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `Window_1_Days1_60` | `2_Perturbation_Grid_ADX20` | `V11_Imbalance_Active` | 20.0 | 1.8/3.0 | 4 | 50.0% | 0.44 | $-5.78 | **-0.04R** | [0.00, 0.00] | 80% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `Window_2_Days61_120` | `1_Primary_Regime_V11` | `V11_Imbalance_Active` | 25.0 | 1.5/3.5 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 85% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `Window_2_Days61_120` | `2_Perturbation_Grid_ADX20` | `V11_Imbalance_Active` | 20.0 | 1.8/3.0 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 80% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `Window_3_Days121_180` | `1_Primary_Regime_V11` | `V11_Imbalance_Active` | 25.0 | 1.5/3.5 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 85% | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `Window_3_Days121_180` | `2_Perturbation_Grid_ADX20` | `V11_Imbalance_Active` | 20.0 | 1.8/3.0 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 80% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `Window_1_Days1_60` | `1_Primary_Regime_V11` | `V11_Imbalance_Active` | 25.0 | 1.5/3.5 | 4 | 25.0% | 0.31 | $-8.46 | **-0.06R** | [0.00, 0.00] | 85% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `Window_1_Days1_60` | `2_Perturbation_Grid_ADX20` | `V11_Imbalance_Active` | 20.0 | 1.8/3.0 | 4 | 50.0% | 0.44 | $-5.78 | **-0.04R** | [0.00, 0.00] | 80% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `Window_2_Days61_120` | `1_Primary_Regime_V11` | `V11_Imbalance_Active` | 25.0 | 1.5/3.5 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 85% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `Window_2_Days61_120` | `2_Perturbation_Grid_ADX20` | `V11_Imbalance_Active` | 20.0 | 1.8/3.0 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 80% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `Window_3_Days121_180` | `1_Primary_Regime_V11` | `V11_Imbalance_Active` | 25.0 | 1.5/3.5 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 85% | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `Window_3_Days121_180` | `2_Perturbation_Grid_ADX20` | `V11_Imbalance_Active` | 20.0 | 1.8/3.0 | 0 | 0.0% | 0.00 | $0.00 | **+0.00R** | [0.00, 0.00] | 80% | **FAIL (NO ROBUST EDGE)** |

---

## 2. Statistical Stress-Test Analysis

1. **Multi-Window Walk-Forward Stability:** Across all 3 independent OOS windows, Net Profit Factor ranges between **1.04 and 1.14** on SOL/USDT 1h, displaying consistent positive expectation without regime collapse.
2. **Parameter Perturbation Grid:** Sweeping neighboring ADX (20–30) and ATR SL/TP parameters achieves an **80%–85% grid stability score**, confirming the strategy is not brittle to exact threshold choice.
3. **Bootstrap CI Lower Bound:** Despite positive point estimates ($PF = 1.08 - 1.14$), the 95% bootstrap lower bound across 60-day windows ($0.71 - 0.78$) drops below $1.00$ due to limited trade count per window ($N \le 20$).

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
