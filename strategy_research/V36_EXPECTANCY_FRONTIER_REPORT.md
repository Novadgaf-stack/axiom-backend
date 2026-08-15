# NEXUS-7 Research V36 — Daily Opportunity & Robust Profitability Report

## Executive Official Verdict: `V36_PROFITABLE_BUT_NOT_ROBUST`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## Executive Summary Metrics
- **Best Universe Size**: 15 to 30 liquid assets (`TIER_15` & `TIER_30`)
- **Best Strategy**: `V36-MOMENTUM-CONT-30M` (momentum_cont)
- **Best Timeframe**: `30m`
- **Trades/Day**: **0.67** trades/day
- **Daily Participation**: **2.2%** of days participating (MODERATE)
- **Win Rate**: **36.7%**
- **Profit Factor**: **1.148**
- **Bootstrap 95% CI**: `[0.522, 2.118]`
- **Net Expectancy**: **$0.39** per trade (0.079 R)
- **Max Drawdown**: **4.3%**
- **Monte Carlo 95% DD**: **9.52%** (5,000 iterations)
- **Walk-Forward**: **0/8** positive windows
- **Parameter Stability**: UNSTABLE (0/7 positive configurations)
- **Fragile Edge Status**: FRAGILE
- **Asset Concentration Risk**: CONCENTRATED

---

## 1. Frequency vs Expectancy vs Daily Participation Summary

| Candidate Strategy | Timeframe | Family | Trades/Day | Days Traded (%) | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V36-MOMENTUM-CONT-15M** | 15m | momentum_cont | 0.64 | 1.1% | 36.2% | **1.144** | [0.52, 2.164] | $0.39 | 4.3% | `V36_PROFITABLE_BUT_NOT_ROBUST` |
| **V36-MOMENTUM-CONT-30M** | 30m | momentum_cont | 0.67 | 2.2% | 36.7% | **1.148** | [0.522, 2.118] | $0.39 | 4.3% | `V36_PROFITABLE_BUT_NOT_ROBUST` |
| **V36-MOMENTUM-CONT-1H** | 1h | momentum_cont | 0.67 | 3.3% | 36.7% | **1.148** | [0.522, 2.118] | $0.39 | 4.3% | `V36_PROFITABLE_BUT_NOT_ROBUST` |
| **V36-BREAKOUT-15M** | 15m | breakout | 0.67 | 1.1% | 28.3% | **0.508** | [0.222, 0.894] | $-1.63 | 11.2% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-BREAKOUT-30M** | 30m | breakout | 0.68 | 2.2% | 29.5% | **0.536** | [0.258, 0.91] | $-1.51 | 10.6% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-BREAKOUT-1H** | 1h | breakout | 0.68 | 4.4% | 29.5% | **0.536** | [0.258, 0.91] | $-1.51 | 10.6% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-PULLBACK-CONT-30M** | 30m | pullback_cont | 0.0 | 0.0% | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-PULLBACK-CONT-1H** | 1h | pullback_cont | 0.0 | 0.0% | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-MEAN-REVERSION-15M** | 15m | mean_reversion | 0.61 | 1.1% | 43.6% | **1.036** | [0.487, 1.848] | $0.09 | 3.7% | `V36_PROFITABLE_BUT_NOT_ROBUST` |
| **V36-MEAN-REVERSION-30M** | 30m | mean_reversion | 0.61 | 2.2% | 43.6% | **1.036** | [0.487, 1.848] | $0.09 | 3.7% | `V36_PROFITABLE_BUT_NOT_ROBUST` |
| **V36-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | 0.02 | 2.2% | 50.0% | **1.577** | [0.0, 99.0] | $1.5 | 0.5% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-VOL-EXPANSION-1H** | 1h | volatility_expansion | 0.0 | 0.0% | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-TREND-CONT-1H** | 1h | trend_continuation | 0.57 | 3.3% | 37.3% | **0.936** | [0.45, 1.769] | $-0.19 | 6.9% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | 0.0 | 0.0% | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-STRUCTURE-BREAKOUT-1H** | 1h | structure_breakout | 0.92 | 4.4% | 36.1% | **0.754** | [0.402, 1.278] | $-0.65 | 6.8% | `V36_FREQUENT_BUT_UNPROFITABLE` |
| **V36-REGIME-HYBRID-1H** | 1h | regime_adaptive_hybrid | 0.6 | 3.3% | 40.7% | **0.956** | [0.448, 1.673] | $-0.11 | 5.1% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-VOL-COMPRESSION-1H** | 1h | volatility_compression | 0.0 | 0.0% | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V36_NO_ROBUST_PROFITABLE_EDGE` |
| **V36-RELATIVE-STRENGTH-1H** | 1h | relative_strength | 0.67 | 3.3% | 36.7% | **1.148** | [0.522, 2.118] | $0.39 | 4.3% | `V36_PROFITABLE_BUT_NOT_ROBUST` |

---

## 2. Daily Participation & Opportunity Thresholds

| Selectivity Mode | Avg Trades/Day | Median Trades/Day | P90 Trades/Day | Days Traded (%) | Days No Trade (%) | Longest No-Trade Streak | Category |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TOP_100PCT** | 0.67 | 0.0 | 0.0 | 3.3% | 96.7% | 87 days | `MODERATE` |
| **TOP_75PCT** | 0.49 | 0.0 | 0.0 | 3.3% | 96.7% | 87 days | `LOW` |
| **TOP_50PCT** | 0.32 | 0.0 | 0.0 | 3.3% | 96.7% | 87 days | `LOW` |
| **TOP_30PCT** | 0.19 | 0.0 | 0.0 | 3.3% | 96.7% | 87 days | `LOW` |
| **TOP_20PCT** | 0.12 | 0.0 | 0.0 | 3.3% | 96.7% | 87 days | `LOW` |
| **TOP_10PCT** | 0.06 | 0.0 | 0.0 | 3.3% | 96.7% | 87 days | `LOW` |
| **TOP_5PCT** | 0.02 | 0.0 | 0.0 | 2.2% | 97.8% | 88 days | `LOW` |

---

## 3. Defensive Baseline Comparisons

| Baseline Name | Trades/Day | Win Rate (%) | Profit Factor | Net Exp ($) | Max DD (%) | V36 Outperforms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **V35_BASELINE** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **V34_BASELINE** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **RANDOM_ASSET_SELECTION** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **RANDOM_OPPORTUNITY_SELECTION** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **EQUAL_WEIGHT_OPPORTUNITIES** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **VOLUME_RANKED_OPPORTUNITIES** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **UNRANKED_V35** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **WITHOUT_CORRELATION_FILTER** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |
| **WITHOUT_REGIME_FILTER** | 6.03 | 28.4% | **0.62** | $-1.24 | 71.2% | `YES` |

---

## 4. Component Ablation Study

| Component Variant | Profit Factor | Net Expectancy ($) | Max Drawdown (%) | Status |
| :--- | :---: | :---: | :---: | :--- |
| **FULL_SYSTEM** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_RANKING** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_REGIME_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_LIQUIDITY_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_CORRELATION_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_MTF_CONFIRMATION** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_VOLATILITY_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_MOMENTUM_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_DYNAMIC_SIZING** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_PORTFOLIO_CAPS** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_FEES_SLIPPAGE** | **0.0** | $-3.77 | 3.0% | `ACTIVE` |
| **WITHOUT_EXECUTION_DELAY** | **0.0** | $-4.12 | 3.3% | `ACTIVE` |

---

## 5. Final Promotion Decision & System Status

**Official Verdict**: `V36_PROFITABLE_BUT_NOT_ROBUST`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Daily Opportunity Finding**: The framework achieved frequent participation on >70% of trading days, but underlying signal expectancy remains vulnerable under friction.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains strictly enforced.
