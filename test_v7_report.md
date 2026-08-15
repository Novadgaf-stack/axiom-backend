# NEXUS-7 — MTF-TP DEEP ROBUSTNESS & ATTRIBUTION REPORT (V7)

**Report Generated:** 2026-08-15 07:33:41 UTC  
**Pipeline Evaluation Duration:** 1.54s  
**SAMPLE SIZE EVALUATED:** `5,000 Bars (BTC & ETH)`  
**FINAL ROBUSTNESS VERDICT:** `REJECTED — EDGE UNSTABLE`  
**DEFLATED SHARPE RATIO (DSR):** `0.0%` (REJECTED (Sharpe <= 0))  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Asset Separation & Directional Attribution

| Evaluation Slice | Trades | Win Rate | Net PnL | Profit Factor | Expectancy / Trade | Audit Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **BTC/USDT (5,000 Bars)** | 65 | 32.3% | $-657.40 | 0.76 | $-10.11 | Primary BTC asset run |
| **ETH/USDT (5,000 Bars)** | 88 | 25.0% | $-416.02 | 0.88 | $-4.73 | Cross-asset validation |
| **Long-Only Signals (BTC)** | 1 | 100.0% | $1,555.45 | 99.0 | $1555.45 | Bullish trade attribution |
| **Short-Only Signals (BTC)** | 1 | 0.0% | $-1,606.73 | 0.0 | $-1606.73 | Bearish trade attribution |
| **30% Untouched OOS Holdout** | 18 | 22.2% | $-509.56 | 0.47 | $-28.31 | Pure OOS holdout window |

---

## 2. 27-Point Parameter Neighborhood Sensitivity Grid

- **Tested Parameter Grid**: ADX `[20, 25, 30]`, ATR Ratio `[0.8, 0.9, 1.0]`, Pullback `[0.1%, 0.2%, 0.3%]`  
- **Profitable Grid Variations**: `9 / 27` (`33.3%`)  
- **Parameter Stability Finding**: ❌ Unstable / Point-Estimate Overfit

| Sample Grid Variations | ADX | ATR Ratio | Pullback % | Trades | Win Rate | Net PnL | Profit Factor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Grid Point (20.0, 0.8) | 20.0 | 0.8 | 0.1% | 63 | 34.9% | $-117.92 | 0.95 |
| Grid Point (20.0, 0.8) | 20.0 | 0.8 | 0.2% | 69 | 34.8% | $-56.71 | 0.98 |
| Grid Point (20.0, 0.8) | 20.0 | 0.8 | 0.3% | 79 | 31.6% | $-82.58 | 0.97 |
| Grid Point (20.0, 0.9) | 20.0 | 0.9 | 0.1% | 55 | 32.7% | $-511.33 | 0.80 |
| Grid Point (20.0, 0.9) | 20.0 | 0.9 | 0.2% | 65 | 32.3% | $-657.40 | 0.76 |
| Grid Point (20.0, 0.9) | 20.0 | 0.9 | 0.3% | 73 | 28.8% | $-679.97 | 0.75 |

---

## 3. Cost & Execution Friction Stress Matrix

| Cost Tier | Friction Config | Trades | Win Rate | Net PnL | Expectancy / Trade | Stress Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Tier 1 (Low Cost)** | Maker/Taker + Slippage | 65 | 32.3% | $-612.31 | $-9.42 | ❌ FAILED |
| **Tier 2 (Standard Cost)** | Maker/Taker + Slippage | 65 | 32.3% | $-657.40 | $-10.11 | ❌ FAILED |
| **Tier 3 (Severe Stress)** | Maker/Taker + Slippage | 65 | 32.3% | $-755.15 | $-11.62 | ❌ FAILED |

---

## 4. Benchmark Baseline Comparison

| Benchmark Baseline | Net PnL | Return % | Audit Comparison |
| :--- | :---: | :---: | :--- |
| **Buy & Hold Benchmark** | $12,934.45 | 129.34% | Passive buy & hold baseline |
| **MTF-TP Strategy Run** | $-657.40 | -6.57% | MTF-TP active strategy |
| **No-Trade Control** | $0.00 | 0.0% | Zero activity baseline |
| **Simple Trend (EMA 20/50)** | $-2,586.89 | -25.87% | Unfiltered technical trend following |
| **Random Entries Baseline** | $-750.92 | -7.51% | Monte Carlo random entry control |

---

## 5. Final MTF-TP Robustness Verdict & Mandate

> **FINAL ROBUSTNESS VERDICT: REJECTED — EDGE UNSTABLE**  
> **PARAMETER REGION STABILITY: 33.3% Profitable Grid Points**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

1. **Research Discipline**: MTF-TP was evaluated strictly as a falsifiable hypothesis across 5,000 bars, BTC & ETH separation, 27-grid parameter perturbation, and 3 cost tiers.
2. **Zero Curve-Fitting**: Refusal to alter thresholds preserves zero-false-positive standards.
3. **Next Steps**: Continue researching order flow imbalance and structural micro-edges before any paper/testnet promotion.
