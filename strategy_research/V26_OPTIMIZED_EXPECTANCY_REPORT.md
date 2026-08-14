# NEXUS-7 — V26 OPTIMIZED EXPECTANCY RESEARCH REPORT

**Overall Verdict:** `REJECTED (NO EDGE PROVEN)`

## 1. Executive Summary & Objective
The V26 research framework evaluated 5 strategy families across 9 liquid crypto pairs and 3 timeframes (15m, 30m, 1h).
Rather than forcing an artificial trade-frequency target, V26 focused on discovering a **genuinely profitable 1–2 trades/day strategy**
with `Net PF >= 1.25`, `Bootstrap 95% CI Lower Bound > 1.00`, and positive expectancy on untouched out-of-sample data.

## 2. Out-of-Sample Performance Summary

| Candidate Name | TF | Trades/Day | Win Rate % | Net PF (0.15%) | Net PF (0.30%) | Net Exp (R) | Max DD % | Bootstrap 95% CI | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `MTF_Trend_Pullback` | `30m` | **5.41** | 0.0% | **0.0** | 0.0 | **-0.3R** | 11.45% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |
| `MTF_Trend_Pullback` | `15m` | **10.21** | 0.0% | **0.0** | 0.0 | **-0.3R** | 20.52% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |
| `MTF_Trend_Pullback` | `1h` | **1.87** | 0.0% | **0.0** | 0.0 | **-0.3R** | 4.12% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |
| `Breakout_Volume_Expansion` | `15m` | **6.34** | 0.0% | **0.0** | 0.0 | **-0.3R** | 13.29% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |
| `Breakout_Volume_Expansion` | `30m` | **1.54** | 0.0% | **0.0** | 0.0 | **-0.3R** | 3.39% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |
| `Adaptive_Mean_Reversion` | `30m` | **9.21** | 0.0% | **0.0** | 0.0 | **-0.3R** | 18.71% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |
| `Momentum_Continuation` | `15m` | **22.42** | 0.0% | **0.0** | 0.0 | **-0.3R** | 39.61% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R; Max Drawdown 39.6% > 25.0%)` |
| `Momentum_Continuation` | `30m` | **9.08** | 0.0% | **0.0** | 0.0 | **-0.3R** | 18.47% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |
| `Dynamic_Regime_Filter` | `1h` | **12.23** | 0.0% | **0.0** | 0.0 | **-0.3R** | 24.02% | `[0.0, 0.0]` | `REJECTED (Net PF 0.00 < 1.25; Bootstrap CI Lower Bound 0.00 <= 1.00; Net Expectancy -0.300R <= 0.00R)` |

## 3. Post-Gate Position Sizing Sensitivity (0.5%, 0.75%, 1.0%)

> **Notice:** No candidates passed the statistical out-of-sample gates (`Net PF >= 1.25` and `Bootstrap CI Lower Bound > 1.00`). Per strict research mandates, position sizing sensitivity was NOT applied to unproven strategies to prevent masking weak edge quality with leverage.

## 4. Production Safety Mandate
- Live real-money trading remains **strictly disabled (`TRADING_ENABLED = False`)**.
- **Final System Status:** `REJECTED (NO EDGE PROVEN)`
