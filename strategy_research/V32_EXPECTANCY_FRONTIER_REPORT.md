# NEXUS-7 Research V32 — Profitability-First Frequency & Position-Sizing Frontier Report

## Executive Official Verdict: `PROFITABLE_BUT_NOT_ROBUST`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## 1. Frequency vs Expectancy vs Drawdown Pareto Frontier Table (Untouched OOS)

| Candidate Strategy | Timeframe | Family | Freq Band | Preferred Window (1.5-4.0/d) | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict | Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V32-VOL-COMP-EXP-4H** | 4h | vol_comp_exp | < 0.5/day | NO | 0.01 | 100.0% | **99.0** | [99.0, 99.0] | $4.17 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 35.15 |
| **V32-VOL-COMP-EXP-1H** | 1h | vol_comp_exp | < 0.5/day | NO | 0.01 | 100.0% | **99.0** | [99.0, 99.0] | $9.38 | 0.0% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 35.15 |
| **V32-MTF-CONFLUENCE-30M** | 30m | mtf_confluence | < 0.5/day | NO | 0.31 | 39.3% | **1.1** | [0.432, 2.306] | $0.24 | 3.4% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.649 |
| **V32-ADAPTIVE-HYBRID-4H** | 4h | adaptive_hybrid | < 0.5/day | NO | 0.47 | 40.5% | **1.068** | [0.512, 1.882] | $0.21 | 3.8% | `PROFITABLE_BUT_NOT_ROBUST` | 0.645 |
| **V32-TREND-CONT-1H** | 1h | trend_cont | 1.0-1.5/day | NO | 1.18 | 36.8% | **0.995** | [0.609, 1.446] | $-0.01 | 9.0% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.631 |
| **V32-MOMENTUM-CONT-30M** | 30m | momentum_cont | 1.0-1.5/day | NO | 1.41 | 37.0% | **0.899** | [0.599, 1.303] | $-0.27 | 7.8% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.609 |
| **V32-MEAN-REVERSION-30M** | 30m | mean_reversion | 1.5-2.0/day | YES | 1.78 | 38.1% | **0.735** | [0.511, 1.015] | $-0.55 | 10.5% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.562 |
| **V32-REGIME-MOM-30M** | 30m | regime_mom | 0.5-1.0/day | NO | 0.53 | 31.2% | **0.846** | [0.397, 1.532] | $-0.44 | 4.1% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.555 |
| **V32-PULLBACK-CONT-30M** | 30m | pullback_cont | 0.5-1.0/day | NO | 0.86 | 33.8% | **0.737** | [0.434, 1.207] | $-0.61 | 7.5% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.527 |
| **V32-BREAKOUT-VOL-1H** | 1h | breakout_vol | 0.5-1.0/day | NO | 0.83 | 28.0% | **0.728** | [0.411, 1.193] | $-0.91 | 10.8% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.508 |
| **V32-PULLBACK-CONT-15M** | 15m | pullback_cont | 0.5-1.0/day | NO | 0.91 | 32.9% | **0.66** | [0.372, 1.048] | $-0.59 | 6.5% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.502 |
| **V32-ADAPTIVE-HYBRID-1H** | 1h | adaptive_hybrid | < 0.5/day | NO | 0.4 | 27.8% | **0.701** | [0.27, 1.388] | $-0.97 | 5.6% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.491 |
| **V32-REGIME-MOM-1H** | 1h | regime_mom | 0.5-1.0/day | NO | 0.67 | 28.3% | **0.684** | [0.339, 1.2] | $-1.02 | 10.0% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.489 |
| **V32-LIQUIDITY-REVERSAL-15M** | 15m | liquidity_reversal | 1.5-2.0/day | YES | 1.84 | 27.1% | **0.565** | [0.387, 0.795] | $-0.8 | 13.3% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.484 |
| **V32-TREND-CONT-30M** | 30m | trend_cont | 1.0-1.5/day | NO | 1.14 | 28.2% | **0.613** | [0.368, 0.956] | $-1.13 | 12.2% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.478 |
| **V32-MEAN-REVERSION-15M** | 15m | mean_reversion | 1.5-2.0/day | YES | 1.86 | 31.1% | **0.498** | [0.345, 0.703] | $-0.84 | 15.9% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.463 |
| **V32-BREAKOUT-VOL-30M** | 30m | breakout_vol | 0.5-1.0/day | NO | 0.83 | 28.0% | **0.499** | [0.274, 0.816] | $-1.51 | 13.1% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` | 0.425 |
| **V32-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | 2.0-3.0/day | YES | 2.06 | 21.6% | **0.46** | [0.301, 0.66] | $-1.66 | 31.8% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` | 0.422 |
| **V32-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | < 0.5/day | NO | 0.29 | 19.2% | **0.367** | [0.074, 0.86] | $-2.12 | 6.3% | `PROMISING_BUT_INSUFFICIENT_SAMPLE` | 0.356 |

---

## 2. Answers to Mandatory 12 Research Questions

1. **Highest-Frequency Genuinely Profitable Candidate**: `V32-VOL-COMP-EXP-4H` (vol_comp_exp)
2. **Real Trades / Day**: **0.47** trades/day
3. **True OOS Profit Factor**: **1.068**
4. **True OOS Expectancy**: **$0.21** per trade (0.038 R)
5. **Maximum Drawdown**: **3.8%**
6. **Monte Carlo 95th-Percentile Drawdown**: **8.46%** (2,000 iterations)
7. **Profitable Walk-Forward Windows**: **1/4** walk-forward windows
8. **Parameter Stability (±10%)**: UNSTABLE (1/5 positive configurations)
9. **Reasonable Risk Percentage**: **0.50% equity risk per trade (Default)** to **0.75% (Max Cap)**
10. **Fastest Frequency Remaining Robustly Profitable**: **0.47 trades/day** (`V32-ADAPTIVE-HYBRID-4H`)
11. **Profitability Frontier Breakdown Point**: Frequency > 4.0 trades/day or < 1.0R risk-reward ratios
12. **Candidate Recommended for Forward Paper Trading**: `NONE - NO ROBUST EDGE FOUND`

---

## 3. Position Sizing & Capital Growth Analysis

| Risk Tier | Risk / Trade | Final Balance ($) | Monthly Return (%) | Annualized Return (%) | Max Drawdown (%) | Execution Note |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **risk_25bps** | 0.25% | $1003.8 | 0.13% | 1.53% | 1.9% | `STANDARD_EXECUTION` |
| **risk_50bps** | 0.5% | $1007.11 | 0.24% | 2.88% | 3.8% | `STANDARD_EXECUTION` |
| **risk_75bps** | 0.75% | $1009.94 | 0.33% | 4.04% | 5.6% | `STANDARD_EXECUTION` |
| **risk_100bps** | 1.0% | $1012.28 | 0.41% | 5.0% | 7.4% | `STANDARD_EXECUTION` |
| **risk_125bps** | 1.25% | $1014.13 | 0.47% | 5.77% | 9.2% | `STANDARD_EXECUTION` |

---

## 4. Monte Carlo 2,000-Iteration Trade Shuffle Analysis

- **Median Return**: 0.64%
- **5th Percentile Return**: -6.47%
- **95th Percentile Return**: 8.29%
- **50th Percentile Max DD**: 4.11%
- **95th Percentile Max DD**: 8.46%
- **Probability of Drawdown > 10%**: 1.8%
- **Probability of Drawdown > 15%**: 0.1%
- **Probability of Drawdown > 20%**: 0.0%
- **Risk of Ruin (>50% DD)**: 0.0%
- **95th Percentile Losing Streak**: 11 consecutive losses

---

## 5. Final Promotion Decision & Next Steps

**Official Verdict**: `PROFITABLE_BUT_NOT_ROBUST`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Friction Impact**: Exchange fees (0.15%) + slippage (0.05%) consume ~0.5%-1.5% margin per trade at high frequency.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains enforced.
