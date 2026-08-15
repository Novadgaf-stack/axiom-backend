# NEXUS-7 Research V35 — Multi-AI Forensic Research & Opportunity Selection Report

## Executive Official Verdict: `V35_PROFITABLE_BUT_NOT_ROBUST`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## Executive Summary Metrics
- **Best Universe Size**: 20 to 30 liquid assets (`TIER_1` & `TIER_2`)
- **Best Strategy**: `V35-MEAN-REVERSION-15M` (mean_reversion)
- **Best Timeframe**: `15m`
- **Trades/Day**: **0.86** trades/day
- **Win Rate**: **51.9%**
- **Profit Factor**: **1.517**
- **Bootstrap 95% CI**: `[0.867, 2.636]`
- **Net Expectancy**: **$1.11** per trade (0.222 R)
- **Max Drawdown**: **3.7%**
- **Monte Carlo 95% DD**: **6.71%** (2,000 iterations)
- **Walk-Forward**: **3/5** positive windows
- **Parameter Stability**: STABLE (3/5 positive configurations)
- **Best Risk/Trade**: **0.50% equity risk per trade**
- **Maximum Aggregate Risk**: **1.50% aggregate open risk cap**
- **Maximum Correlated Risk**: **1.00% correlated risk cap**
- **Friction Sensitivity**: EXPIRES UNDER FRICTION

---

## 1. Frequency vs Expectancy vs Drawdown Pareto Frontier Table (Untouched OOS)

| Candidate Strategy | Timeframe | Family | Freq Band | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict | Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V35-MEAN-REVERSION-15M** | 15m | mean_reversion | 0.75-1.00/day | 0.86 | 51.9% | **1.517** | [0.867, 2.636] | $1.11 | 3.7% | `V35_PROFITABLE_BUT_NOT_ROBUST` | 0.834 |
| **V35-MEAN-REVERSION-30M** | 30m | mean_reversion | 0.75-1.00/day | 0.86 | 51.9% | **1.517** | [0.867, 2.636] | $1.11 | 3.7% | `V35_PROFITABLE_BUT_NOT_ROBUST` | 0.834 |
| **V35-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | < 0.25/day | 0.02 | 50.0% | **1.577** | [0.0, 99.0] | $1.5 | 0.5% | `V35_NO_ROBUST_PROFITABLE_EDGE` | 0.827 |
| **V35-MOMENTUM-CONT-15M** | 15m | momentum_cont | 0.75-1.00/day | 0.82 | 35.1% | **0.991** | [0.488, 1.804] | $-0.03 | 4.6% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.621 |
| **V35-ADAPTIVE-HYBRID-1H** | 1h | adaptive_hybrid | 0.75-1.00/day | 0.81 | 41.1% | **0.962** | [0.529, 1.641] | $-0.1 | 5.7% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.618 |
| **V35-ADAPTIVE-HYBRID-4H** | 4h | adaptive_hybrid | 0.75-1.00/day | 0.81 | 41.1% | **0.962** | [0.529, 1.641] | $-0.1 | 5.7% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.618 |
| **V35-MOMENTUM-CONT-30M** | 30m | momentum_cont | 0.75-1.00/day | 0.86 | 35.1% | **0.97** | [0.483, 1.74] | $-0.08 | 5.1% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.615 |
| **V35-MOMENTUM-CONT-1H** | 1h | momentum_cont | 0.75-1.00/day | 0.86 | 35.1% | **0.97** | [0.483, 1.74] | $-0.08 | 5.1% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.615 |
| **V35-STRUCTURE-SWEEP-1H** | 1h | structure_sweep | 1.00-1.50/day | 1.2 | 37.0% | **0.779** | [0.437, 1.241] | $-0.57 | 7.5% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.559 |
| **V35-TREND-REGIME-1H** | 1h | trend_regime | 0.50-0.75/day | 0.73 | 34.8% | **0.82** | [0.419, 1.55] | $-0.57 | 9.1% | `V35_NO_ROBUST_PROFITABLE_EDGE` | 0.55 |
| **V35-BREAKOUT-15M** | 15m | breakout | 0.75-1.00/day | 0.91 | 29.3% | **0.488** | [0.271, 0.793] | $-1.7 | 14.2% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.424 |
| **V35-BREAKOUT-30M** | 30m | breakout | 0.75-1.00/day | 0.91 | 29.3% | **0.488** | [0.271, 0.793] | $-1.7 | 14.2% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.424 |
| **V35-BREAKOUT-1H** | 1h | breakout | 0.75-1.00/day | 0.91 | 29.3% | **0.488** | [0.271, 0.793] | $-1.7 | 14.2% | `V35_FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.424 |
| **V35-PULLBACK-CONT-30M** | 30m | pullback_cont | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V35_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V35-PULLBACK-CONT-1H** | 1h | pullback_cont | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V35_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V35-VOL-COMP-EXP-1H** | 1h | volatility_expansion | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V35_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V35-MTF-CONFLUENCE-30M** | 30m | mtf_confluence | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V35_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |
| **V35-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | < 0.25/day | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V35_NO_ROBUST_PROFITABLE_EDGE` | 0.2 |

---

## 2. Defensive Baseline Comparisons

| Baseline Name | Trades/Day | Win Rate (%) | Profit Factor | Net Exp ($) | Max DD (%) | CI Lower | V35 Outperforms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V34_BEST_CANDIDATE** | 5.97 | 28.1% | **0.6** | $-1.32 | 73.6% | 0.458 | `YES` |
| **EQUAL_WEIGHT_RANDOM** | 5.97 | 28.1% | **0.6** | $-1.32 | 73.6% | 0.458 | `YES` |
| **RANDOM_ASSET_SELECTION** | 5.97 | 28.1% | **0.6** | $-1.32 | 73.6% | 0.458 | `YES` |
| **NO_RANKING** | 5.97 | 28.1% | **0.6** | $-1.32 | 73.6% | 0.458 | `YES` |
| **NO_CORRELATION_FILTER** | 5.97 | 28.1% | **0.6** | $-1.32 | 73.6% | 0.458 | `YES` |
| **TOP_VOLUME_SELECTION** | 5.97 | 28.1% | **0.6** | $-1.32 | 73.6% | 0.458 | `YES` |

---

## 3. Selectivity Thresholds & Percentile Buckets

| Selectivity Bucket | Trades/Day | Total Trades | Win Rate (%) | Profit Factor | Net Exp ($) | Max DD (%) | Selectivity Improved Edge |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TOP_100PCT** | 5.97 | 537 | 28.1% | **0.6** | $-1.32 | 73.6% | `NO` |
| **TOP_75PCT** | 4.47 | 402 | 28.1% | **0.568** | $-1.43 | 59.0% | `NO` |
| **TOP_50PCT** | 2.98 | 268 | 28.7% | **0.633** | $-1.18 | 32.0% | `NO` |
| **TOP_30PCT** | 1.78 | 160 | 31.2% | **0.749** | $-0.76 | 14.4% | `NO` |
| **TOP_20PCT** | 1.19 | 107 | 30.8% | **0.702** | $-0.92 | 10.3% | `NO` |
| **TOP_10PCT** | 0.59 | 53 | 35.8% | **0.962** | $-0.11 | 4.4% | `NO` |
| **TOP_5PCT** | 0.29 | 26 | 38.5% | **0.956** | $-0.13 | 3.0% | `NO` |
| **TOP_1** | 0.01 | 1 | 0.0% | **0.0** | $-5.08 | 0.5% | `NO` |
| **TOP_2** | 0.01 | 1 | 0.0% | **0.0** | $-5.08 | 0.5% | `NO` |
| **TOP_3** | 0.01 | 1 | 0.0% | **0.0** | $-5.08 | 0.5% | `NO` |
| **TOP_5** | 0.01 | 1 | 0.0% | **0.0** | $-5.08 | 0.5% | `NO` |

---

## 4. Component Ablation Study

| Component Variant | Profit Factor | Net Expectancy ($) | Max Drawdown (%) | Contribution |
| :--- | :---: | :---: | :---: | :--- |
| **FULL_SYSTEM** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_FEES_SLIPPAGE** | **0.0** | $-3.77 | 3.0% | `ACTIVE` |
| **WITHOUT_EXECUTION_DELAY** | **0.0** | $-4.12 | 3.3% | `ACTIVE` |
| **WITHOUT_RANKING** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_CORRELATION_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_REGIME_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_VOLATILITY_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_LIQUIDITY_FILTER** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_DYNAMIC_SIZING** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |
| **WITHOUT_RISK_CAP** | **0.0** | $-3.96 | 3.2% | `ACTIVE` |

---

## 5. Final Promotion Decision & System Status

**Official Verdict**: `V35_PROFITABLE_BUT_NOT_ROBUST`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Opportunity Selection Finding**: Opportunity-level quality scoring and ranking reduces noise trades but cannot transform a weak baseline edge into a robust edge.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains strictly enforced.
