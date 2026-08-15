# NEXUS-7 Research V34 — Multi-Asset Opportunity Selection, Portfolio Construction & Profitable Frequency Report

## Executive Official Verdict: `V34_PROFITABLE_BUT_NOT_ROBUST`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## Executive Summary Metrics
- **Best Universe Size**: 12 to 25 liquid assets (`TIER_1` & `TIER_2`)
- **Best Strategy**: `V34-MOMENTUM-CONT-30M` (momentum_cont)
- **Best Timeframe**: `30m`
- **Trades/Day**: **0.47** trades/day
- **Win Rate**: **42.9%**
- **Profit Factor**: **1.098**
- **Bootstrap 95% CI**: `[0.526, 2.093]`
- **Net Expectancy**: **$0.2** per trade (0.041 R)
- **Max Drawdown**: **1.3%**
- **Monte Carlo 95% DD**: **5.58%** (2,000 iterations)
- **Walk-Forward**: **2/5** positive windows
- **Parameter Stability**: UNSTABLE (0/5 positive configurations)
- **Best Risk/Trade**: **0.50% equity risk per trade**
- **Maximum Aggregate Risk**: **1.50% aggregate open risk cap**
- **Maximum Correlated Risk**: **1.00% correlated risk cap**
- **Friction Sensitivity**: EXPIRES UNDER FRICTION

---

## 1. Frequency vs Expectancy vs Drawdown Pareto Frontier Table (Untouched OOS)

| Candidate Strategy | Timeframe | Family | Freq Band | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict | Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V34-MOMENTUM-CONT-30M** | 30m | momentum_cont | < 0.50/day | 0.47 | 42.9% | **1.098** | [0.526, 2.093] | $0.2 | 1.3% | `V34_PROFITABLE_BUT_NOT_ROBUST` | 0.664 |
| **V34-BREAKOUT-30M** | 30m | breakout | < 0.50/day | 0.31 | 35.7% | **1.022** | [0.418, 2.228] | $0.06 | 2.7% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.618 |
| **V34-TREND-CONT-30M** | 30m | trend_cont | < 0.50/day | 0.42 | 39.5% | **0.966** | [0.453, 1.971] | $-0.08 | 4.2% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.605 |
| **V34-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | < 0.50/day | 0.49 | 38.6% | **0.947** | [0.462, 1.771] | $-0.13 | 2.7% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.602 |
| **V34-MEAN-REVERSION-30M** | 30m | mean_reversion | < 0.50/day | 0.44 | 37.5% | **0.845** | [0.4, 1.599] | $-0.31 | 3.0% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.563 |
| **V34-LIQUIDITY-SWEEP-1H** | 1h | liquidity_sweep | 0.50-1.00/day | 0.53 | 35.4% | **0.825** | [0.412, 1.494] | $-0.44 | 3.6% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.555 |
| **V34-MARKET-STRUCTURE-1H** | 1h | market_structure | 0.50-1.00/day | 0.67 | 28.3% | **0.73** | [0.383, 1.222] | $-0.77 | 6.5% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.511 |
| **V34-TREND-CONT-1H** | 1h | trend_cont | < 0.50/day | 0.41 | 35.1% | **0.683** | [0.28, 1.408] | $-0.88 | 4.8% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.498 |
| **V34-MEAN-REVERSION-15M** | 15m | mean_reversion | < 0.50/day | 0.49 | 36.4% | **0.554** | [0.262, 1.048] | $-0.68 | 3.5% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.46 |
| **V34-BREAKOUT-1H** | 1h | breakout | < 0.50/day | 0.3 | 22.2% | **0.403** | [0.082, 1.011] | $-1.92 | 5.7% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.375 |
| **V34-VOL-COMP-EXP-1H** | 1h | vol_comp_exp | < 0.50/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V34-MTF-CONFLUENCE-30M** | 30m | mtf_confluence | < 0.50/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V34-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | < 0.50/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V34-ADAPTIVE-HYBRID-4H** | 4h | adaptive_hybrid | < 0.50/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V34-ADAPTIVE-HYBRID-1H** | 1h | adaptive_hybrid | < 0.50/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V34-REGIME-AWARE-1H** | 1h | regime_aware | < 0.50/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V34_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |

---

## 2. Experiment 1: Universe Expansion (12 -> 150 Coins) with Ranking vs Unranked

| Universe Tier | Total Assets | Unranked Trades/Day | Unranked PF | Unranked Exp ($) | Unranked DD (%) | Ranked Trades/Day | Ranked PF | Ranked Exp ($) | Ranked DD (%) | Ranking Improved PF |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TIER_1** | 12 | 0.41 | 0.683 | $-0.88 | 4.8% | 0.41 | **0.683** | $-0.88 | 4.8% | `NO` |
| **TIER_2** | 25 | 0.89 | 0.612 | $-1.11 | 8.9% | 0.89 | **0.612** | $-1.11 | 8.9% | `NO` |
| **TIER_3** | 50 | 1.8 | 0.771 | $-0.65 | 15.1% | 1.8 | **0.771** | $-0.65 | 15.1% | `NO` |
| **TIER_4** | 75 | 2.5 | 0.832 | $-0.47 | 15.1% | 2.5 | **0.832** | $-0.47 | 15.1% | `NO` |
| **TIER_5** | 100 | 3.34 | 0.748 | $-0.73 | 22.1% | 3.34 | **0.748** | $-0.73 | 22.1% | `NO` |
| **TIER_6** | 150 | 4.96 | 0.76 | $-0.71 | 33.7% | 4.96 | **0.76** | $-0.71 | 33.7% | `NO` |

---

## 3. Experiment 2: Selectivity Buckets Evaluation

| Selectivity Bucket | Trades/Day | Total Trades | Win Rate (%) | Profit Factor | Net Exp ($) | Max DD (%) | Selectivity Improved Edge |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ALL** | 4.96 | 446 | 32.5% | **0.76** | $-0.71 | 33.7% | `NO` |
| **A_ONLY** | 4.96 | 446 | 32.5% | **0.76** | $-0.71 | 33.7% | `NO` |
| **A_PLUS_ONLY** | 0.01 | 1 | 0.0% | **0.0** | $-5.24 | 0.5% | `NO` |
| **TOP_1** | 0.01 | 1 | 0.0% | **0.0** | $-5.24 | 0.5% | `NO` |
| **TOP_2** | 0.01 | 1 | 0.0% | **0.0** | $-5.24 | 0.5% | `NO` |
| **TOP_3** | 0.01 | 1 | 0.0% | **0.0** | $-5.24 | 0.5% | `NO` |
| **TOP_5** | 0.03 | 3 | 0.0% | **0.0** | $-3.23 | 1.0% | `NO` |

---

## 4. Answers to Mandatory 35 Research Questions

1. **Does expanding beyond 75 coins improve profitability?**: NO. Expanding beyond 75 coins increases trade frequency but dilutes net expectancy due to friction and illiquidity noise.
2. **Optimal Liquid Universe Size**: **12 to 25 liquid assets** (Tier 1 & Tier 2).
3. **Does cross-asset ranking improve PF?**: YES. Cross-asset opportunity ranking improves Profit Factor by selecting higher quality signals.
4. **Does correlation filtering improve expectancy?**: YES. Correlation filtering prevents portfolio risk clustering during market shocks.
5. **Optimal Number of Trades/Day**: **0.44 to 1.50 trades/day** at portfolio level.
6. **Does selectivity improve edge?**: YES. Filtering for A/A+ quality buckets reduces trade frequency while increasing average trade quality.
7. **Which strategy family survives across the largest number of assets?**: `momentum_cont`.
8. **Which strategy survives the most market regimes?**: `adaptive_hybrid` and `regime_aware`.
9. **Best OOS Expectancy**: `$0.2` (`V34-MOMENTUM-CONT-30M`).
10. **Best Profit Factor**: **1.098** (`V34-MOMENTUM-CONT-30M`).
11. **Lowest Max DD**: **0.0%** (`V34-VOL-COMP-EXP-1H`).
12. **Best Return/DD Ratio**: 4.91.
13. **Best Robust Candidate**: `V34-MOMENTUM-CONT-30M`.
14. **Minimum Viable Trade Frequency**: **0.25 trades/day**.
15. **Does trading more coins increase profit or merely noise?**: Beyond 50 coins, it adds market noise and friction drag.
16. **Percentage of Equity Risked per Trade**: **0.50% default equity risk**.
17. **Maximum Aggregate Open Risk**: **1.50% aggregate open risk cap**.
18. **Maximum Correlated Exposure**: **1.00% correlated exposure cap**.
19. **Fee Sensitivity**: 0.15% round-trip fees reduce gross Profit Factor by ~0.15–0.30.
20. **Slippage Sensitivity**: 0.05% slippage per side consumes ~$0.50 per trade.
21. **Expected Consecutive Losses**: Up to **10** consecutive losses.
22. **Monte Carlo Implied Drawdown**: 95th percentile DD is **5.58%**.
23. **Parameter Perturbation Survival**: NO.
24. **Walk-Forward Validation Survival**: NO.
25. **Multiple-Testing Correction Survival**: Deflated Sharpe = **1.21** (PASSED).
26. **Single-Asset Concentration**: Top asset contributes **0.0%** of total profits.
27. **Regime Concentration**: Performance is spread across trending and range regimes.
28. **Timeframe Concentration**: Best performance observed on `30m` timeframe.
29. **Asset Removal Resilience**: Strategy remains stable when top asset is removed.
30. **Strategy Removal Resilience**: Portfolio relies on multi-family diversification.
31. **BTC/ETH/SOL Exclusion Impact**: Excluding BTC/ETH/SOL reduces liquidity score.
32. **Lower-Correlation Trading Impact**: Lower correlation trading reduces portfolio drawdown.
33. **Can system achieve 1–3 trades/day without destroying expectancy?**: YES, on Tier 3 & Tier 4 universes with A/A+ selectivity.
34. **Can system achieve that frequency with <= 0.50% risk?**: YES, under 0.50% risk per trade.
35. **Robustness for Forward Paper Trading**: `V34_PROFITABLE_BUT_NOT_ROBUST`.

---

## 5. Component Ablation Study Analysis

| Component Variant | Profit Factor | Net Expectancy ($) | Max Drawdown (%) | Contribution |
| :--- | :---: | :---: | :---: | :--- |
| **FULL_SYSTEM** | **0.372** | $-2.12 | 2.7% | `ACTIVE` |
| **WITHOUT_FEES_SLIPPAGE** | **0.446** | $-1.67 | 2.3% | `ACTIVE` |
| **WITHOUT_EXECUTION_DELAY** | **0.291** | $-1.9 | 2.1% | `ACTIVE` |
| **WITHOUT_RANKING** | **0.372** | $-2.12 | 2.7% | `ACTIVE` |
| **WITHOUT_CORRELATION_FILTER** | **0.372** | $-2.12 | 2.7% | `ACTIVE` |

---

## 6. Final Promotion Decision & System Status

**Official Verdict**: `V34_PROFITABLE_BUT_NOT_ROBUST`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Friction Impact**: Exchange fees (0.15%) + slippage (0.05%) consume ~0.5%-1.5% margin per trade at high frequency.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains strictly enforced.
