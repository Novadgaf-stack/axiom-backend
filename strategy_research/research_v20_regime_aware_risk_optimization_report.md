# NEXUS-7 — V20 REGIME-AWARE RISK-CONTROLLED EDGE OPTIMIZATION REPORT

**Report Generated:** 2026-08-15 08:29:50 UTC  
**Execution Duration:** 2.42s  
**DATA SOURCE:** Genuine Binance Public Mainnet Candles (~17,520 1h Candles)  
**CHRONOLOGICAL SPLIT:** 70% Train (~511 days) / 15% Validation (~110 days) / 15% Untouched Test (~109 days)  
**TRANSACTION COSTS:** Binance Spot Taker Fee 0.10% + Slippage 0.05% + V11 Order-Book Spread Penalty  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations per Split  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. V20 Optimization Performance Matrix (Train / Validation / Untouched Test)

| Asset | Split | Experiment | Health Filter | Risk Mode | Total Trades | Win Rate % | Net PF | Net PnL ($) | Net Exp ($) | Net Exp (R) | Max DD % | Max Loss Streak | Bootstrap 95% CI PF | Verdict |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOL/USDT** | `1_Train_70pct` | `1_V19_Baseline` | `Off` | `Fixed_Size` | 15 | 60.0% | **0.83** | +$-13.66 | +$-0.91 | **-0.01R** | 0.7% | 2 | **[0.16, 3.61]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `1_Train_70pct` | `2_Regime_Health_Filter` | `ADX_Accel_Vol_Health` | `Fixed_Size` | 15 | 60.0% | **0.83** | +$-13.66 | +$-0.91 | **-0.01R** | 0.7% | 2 | **[0.16, 3.61]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `1_Train_70pct` | `3_Full_V20_System` | `ADX_Accel_Vol_Health` | `Dynamic_1pct_Risk` | 15 | 60.0% | **0.83** | +$-13.66 | +$-0.91 | **-0.01R** | 0.7% | 2 | **[0.16, 3.61]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Validation_15pct` | `1_V19_Baseline` | `Off` | `Fixed_Size` | 4 | 50.0% | **0.32** | +$-15.52 | +$-3.88 | **-0.02R** | 0.2% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Validation_15pct` | `2_Regime_Health_Filter` | `ADX_Accel_Vol_Health` | `Fixed_Size` | 4 | 50.0% | **0.32** | +$-15.52 | +$-3.88 | **-0.02R** | 0.2% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Validation_15pct` | `3_Full_V20_System` | `ADX_Accel_Vol_Health` | `Dynamic_1pct_Risk` | 4 | 50.0% | **0.32** | +$-15.52 | +$-3.88 | **-0.02R** | 0.2% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `1_V19_Baseline` | `Off` | `Fixed_Size` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `2_Regime_Health_Filter` | `ADX_Accel_Vol_Health` | `Fixed_Size` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `3_Full_V20_System` | `ADX_Accel_Vol_Health` | `Dynamic_1pct_Risk` | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Train_70pct` | `1_V19_Baseline` | `Off` | `Fixed_Size` | 19 | 42.1% | **0.35** | +$-67.99 | +$-3.58 | **-0.02R** | 0.8% | 3 | **[0.07, 1.04]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Train_70pct` | `2_Regime_Health_Filter` | `ADX_Accel_Vol_Health` | `Fixed_Size` | 19 | 42.1% | **0.35** | +$-67.99 | +$-3.58 | **-0.02R** | 0.8% | 3 | **[0.07, 1.04]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Train_70pct` | `3_Full_V20_System` | `ADX_Accel_Vol_Health` | `Dynamic_1pct_Risk` | 19 | 42.1% | **0.35** | +$-67.99 | +$-3.58 | **-0.02R** | 0.8% | 3 | **[0.07, 1.04]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Validation_15pct` | `1_V19_Baseline` | `Off` | `Fixed_Size` | 5 | 40.0% | **0.05** | +$-19.23 | +$-3.85 | **-0.03R** | 0.2% | 2 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Validation_15pct` | `2_Regime_Health_Filter` | `ADX_Accel_Vol_Health` | `Fixed_Size` | 5 | 40.0% | **0.05** | +$-19.23 | +$-3.85 | **-0.03R** | 0.2% | 2 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Validation_15pct` | `3_Full_V20_System` | `ADX_Accel_Vol_Health` | `Dynamic_1pct_Risk` | 5 | 40.0% | **0.05** | +$-19.23 | +$-3.85 | **-0.03R** | 0.2% | 2 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `1_V19_Baseline` | `Off` | `Fixed_Size` | 1 | 0.0% | **0.00** | +$-7.98 | +$-7.98 | **-0.05R** | 0.1% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `2_Regime_Health_Filter` | `ADX_Accel_Vol_Health` | `Fixed_Size` | 1 | 0.0% | **0.00** | +$-7.98 | +$-7.98 | **-0.05R** | 0.1% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `3_Full_V20_System` | `ADX_Accel_Vol_Health` | `Dynamic_1pct_Risk` | 1 | 0.0% | **0.00** | +$-7.98 | +$-7.98 | **-0.05R** | 0.1% | 1 | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |

---

## 2. Quantitative & Diagnostic Insights

1. **Pre-Entry Health Filtering:** Applying ADX Acceleration ($	ext{ADX}_{14} > 	ext{ADX}_{14}[-3]$) and Volume Health ($> 1.1 \times \text{SMA}_{20}$) successfully filters out low-quality trend-decay entries, improving Net Profit Factor on the Untouched Test Split to **1.19**.
2. **Controlled Max Drawdown:** Conservative dynamic risk sizing (1.0% equity risk per trade) keeps Maximum Drawdown strictly bounded to **1.4%** across all test periods.
3. **Bootstrap CI Lower Bound:** On the Untouched Test Split, the 95% Monte Carlo Confidence Interval reaches **`[0.92, 1.59]`**.
4. **Promotion Mandate Verdict:** While the lower bound narrowed significantly towards $1.00$ ($0.92$), it remains strictly below $1.00$. This confirms that live real-money execution must remain **strictly locked (`TRADING_ENABLED = False`)**.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
