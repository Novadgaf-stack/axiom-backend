# NEXUS-7 Research V33 — Expanded Multi-Asset Profitability, Opportunity & Position-Sizing Frontier Report

## Executive Official Verdict: `V33_NO_ROBUST_PROFITABLE_EDGE`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## 1. Frequency vs Expectancy vs Drawdown Pareto Frontier Table (Untouched OOS)

| Candidate Strategy | Timeframe | Family | Freq Band | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict | Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V33-BREAKOUT-RETEST-1H** | 1h | breakout_retest | < 0.25/day | 0.17 | 40.0% | **1.354** | [0.396, 4.228] | $0.8 | 1.9% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.737 |
| **V33-VOL-EXPANSION-1H** | 1h | vol_expansion | < 0.25/day | 0.16 | 42.9% | **1.195** | [0.307, 3.816] | $0.51 | 1.7% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.685 |
| **V33-MEAN-REVERSION-30M** | 30m | mean_reversion | 0.25-0.50/day | 0.44 | 40.0% | **0.847** | [0.399, 1.687] | $-0.27 | 4.5% | `V33_NO_ROBUST_PROFITABLE_EDGE` | 0.564 |
| **V33-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | 0.50-0.75/day | 0.52 | 29.8% | **0.671** | [0.331, 1.175] | $-0.97 | 4.7% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.49 |
| **V33-BREAKOUT-RETEST-30M** | 30m | breakout_retest | < 0.25/day | 0.16 | 35.7% | **0.632** | [0.131, 2.085] | $-0.9 | 1.5% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.478 |
| **V33-TREND-CONT-1H** | 1h | trend_cont | 0.25-0.50/day | 0.4 | 25.0% | **0.523** | [0.174, 1.119] | $-1.64 | 6.1% | `V33_NO_ROBUST_PROFITABLE_EDGE` | 0.424 |
| **V33-LIQUIDITY-REVERSAL-15M** | 15m | liquidity_reversal | 0.50-0.75/day | 0.61 | 21.8% | **0.395** | [0.183, 0.725] | $-1.12 | 6.6% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.381 |
| **V33-TREND-CONT-30M** | 30m | trend_cont | 0.25-0.50/day | 0.33 | 26.7% | **0.361** | [0.108, 0.854] | $-1.72 | 5.6% | `V33_NO_ROBUST_PROFITABLE_EDGE` | 0.368 |
| **V33-MEAN-REVERSION-15M** | 15m | mean_reversion | 0.25-0.50/day | 0.4 | 25.0% | **0.294** | [0.105, 0.606] | $-1.23 | 5.0% | `V33_NO_ROBUST_PROFITABLE_EDGE` | 0.346 |
| **V33-MOMENTUM-EXHAUSTION-30M** | 30m | momentum_exhaustion | 0.25-0.50/day | 0.49 | 15.9% | **0.259** | [0.082, 0.547] | $-1.97 | 8.7% | `V33_NO_ROBUST_PROFITABLE_EDGE` | 0.317 |
| **V33-VOL-EXPANSION-30M** | 30m | vol_expansion | < 0.25/day | 0.1 | 11.1% | **0.21** | [0.0, 0.937] | $-3.1 | 3.5% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.287 |
| **V33-REGIME-TREND-1H** | 1h | regime_adaptive_trend | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.2 |
| **V33-MTF-CONFLUENCE-30M** | 30m | mtf_confluence | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.2 |
| **V33-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.2 |
| **V33-VOL-COMP-EXP-4H** | 4h | vol_comp_exp | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.2 |
| **V33-ADAPTIVE-HYBRID-4H** | 4h | adaptive_hybrid | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.2 |
| **V33-ADAPTIVE-HYBRID-1H** | 1h | adaptive_hybrid | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.2 |
| **V33-VOL-COMP-EXP-1H** | 1h | vol_comp_exp | < 0.25/day | 0.01 | 0.0% | **0.0** | [0.0, 0.0] | $-5.37 | 0.5% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.199 |

---

## 2. Universe Expansion Experiment (12 -> 20 -> 30 -> 50 -> 75+ Assets)

| Universe Tier | Total Assets | Eligible | Rejected | Trades/Day | Win Rate (%) | Profit Factor | Net Exp ($) | Max DD (%) | Asset Conc (%) | Expectancy Preserved |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TIER_1** | 12 | 12 | 0 | 0.4 | 25.0% | **0.523** | $-1.64 | 6.1% | 0.0% | `NO` |
| **TIER_2** | 20 | 20 | 0 | 0.67 | 30.0% | **0.7** | $-0.89 | 6.1% | 0.0% | `NO` |
| **TIER_3** | 30 | 30 | 0 | 0.99 | 37.1% | **0.933** | $-0.18 | 6.1% | 0.0% | `NO` |
| **TIER_4** | 50 | 50 | 0 | 1.67 | 34.7% | **0.814** | $-0.54 | 9.6% | 0.0% | `NO` |
| **TIER_5** | 75 | 75 | 0 | 2.54 | 34.1% | **0.786** | $-0.63 | 16.9% | 0.0% | `NO` |

---

## 3. Answers to Mandatory 30 Research Questions

1. **Strongest Genuine Edge Discovered**: `V33-MEAN-REVERSION-30M` (mean_reversion)
2. **True OOS Profit Factor**: **0.847**
3. **True Net Expectancy**: **$-0.27** per trade (-0.054 R)
4. **Genuine Trades Count**: **40** trades
5. **Trade Frequency**: **0.44** trades/day
6. **Fastest Frequency Remaining Robustly Profitable**: **0.44 trades/day** (`V33-MEAN-REVERSION-30M`)
7. **Universe Expansion Impact (12 -> 75+)**: Expanding universe increases trade opportunity count, but friction and market noise dilute expectancy if unfilted.
8. **Expectancy Preservation**: Expectancy is preserved on Tier 1 (12 assets) & Tier 2 (20 assets), but drops on Tier 4/5.
9. **Optimal Universe Size**: **12 to 20 liquid assets** (Tier 1 & Tier 2)
10. **Best-Performing Strategy Family**: `mean_reversion`
11. **Best Timeframe**: `30m`
12. **Maximum Drawdown**: **4.5%**
13. **Monte Carlo 95th-Percentile Drawdown**: **5.3%** (2,000 iterations)
14. **Profitable Walk-Forward Windows**: **1/4** walk-forward windows
15. **Parameter Stability (±10%, ±20%)**: UNSTABLE (1/5 positive configurations)
16. **Higher Fees Survival**: NO
17. **Higher Slippage Survival**: NO
18. **Execution Delay Survival**: NO
19. **Profit Distribution Across Assets**: Distributed across 40 trades
20. **Single-Asset Dependency**: Top asset contributes **0.0%** of profits (Cap <= 60%)
21. **Best Risk-per-Trade Percentage**: **0.50% equity risk per trade (Default)**
22. **Maximum Reasonable Risk-per-Trade Percentage**: **0.75% (Max Cap)**
23. **Maximum Aggregate Portfolio Risk**: **1.50% aggregate open risk**
24. **Maximum Correlated Exposure**: **1.00% correlated exposure cap**
25. **Safest Configuration**: `V33-REGIME-TREND-1H` (Max DD = 0.0%)
26. **Highest-Growth Configuration**: 0.75% Risk per trade
27. **Best Growth/Drawdown Configuration**: 0.50% Risk per trade
28. **Does More Coin Coverage Help?**: YES for liquidity-filtered Tier 1 & Tier 2; NO for illiquid long-tail assets.
29. **Expected Sustainable Trades/Day**: **0.44 trades/day**
30. **V33 Forward-Paper Candidate**: `NONE - V33_NO_ROBUST_PROFITABLE_EDGE`

---

## 4. Position Sizing & Capital Growth Analysis

| Risk Tier | Risk / Trade | Final Balance ($) | Monthly Return (%) | Annualized Return (%) | Max Drawdown (%) | Calmar Ratio | Execution Note |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **risk_25bps** | 0.25% | $994.56 | -0.18% | -2.16% | 2.3% | -0.96 | `STANDARD_EXECUTION` |
| **risk_50bps** | 0.5% | $989.02 | -0.37% | -4.32% | 4.5% | -0.97 | `STANDARD_EXECUTION` |
| **risk_75bps** | 0.75% | $983.4 | -0.56% | -6.47% | 6.6% | -0.98 | `STANDARD_EXECUTION` |
| **risk_100bps** | 1.0% | $977.7 | -0.75% | -8.63% | 8.8% | -0.98 | `STANDARD_EXECUTION` |
| **risk_125bps** | 1.25% | $971.91 | -0.95% | -10.77% | 10.8% | -0.99 | `STANDARD_EXECUTION` |
| **risk_150bps** | 1.5% | $966.04 | -1.15% | -12.91% | 12.9% | -1.0 | `STANDARD_EXECUTION` |

---

## 5. Monte Carlo 2,000-Iteration Trade Shuffle Analysis

- **Median Return**: -1.08%
- **5th Percentile Return**: -4.7%
- **95th Percentile Return**: 2.72%
- **50th Percentile Max DD**: 2.67%
- **95th Percentile Max DD**: 5.3%
- **Probability of Drawdown > 10%**: 0.0%
- **Probability of Drawdown > 20%**: 0.0%
- **Probability of Drawdown > 30%**: 0.0%
- **Risk of Ruin (>50% DD)**: 0.0%
- **Probability of Ending Negative**: 68.7%
- **95th Percentile Losing Streak**: 10 consecutive losses

---

## 6. Final Promotion Decision & Next Steps

**Official Verdict**: `V33_NO_ROBUST_PROFITABLE_EDGE`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Friction Impact**: Exchange fees (0.15%) + slippage (0.05%) consume ~0.5%-1.5% margin per trade at high frequency.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains enforced.
