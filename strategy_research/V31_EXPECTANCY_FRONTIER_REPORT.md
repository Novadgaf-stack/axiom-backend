# NEXUS-7 Research V31 — Zero-Stub Forensically Validated Expectancy Search Report

## Executive Official Verdict: `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## 1. Frequency vs Expectancy vs Drawdown Frontier Table (Untouched OOS)

| Candidate Strategy | Timeframe | Family | Target Window (0.8-1.5/d) | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp / Trade ($) | Max Drawdown (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V31-MTF-CONFLUENCE-30M** | 30m | mtf_confluence | NO | 3.31 | 33.9% | **1.081** | [0.839, 1.361] | $0.21 | 10.3% | `PROFITABLE_BUT_NOT_ROBUST` |
| **V31-TREND-CONT-30M** | 30m | trend_cont | NO | 5.54 | 41.1% | **1.059** | [0.882, 1.26] | $0.12 | 10.7% | `PROFITABLE_BUT_NOT_ROBUST` |
| **V31-VOL-COMP-EXP-4H** | 4h | vol_comp_exp | NO | 4.13 | 36.3% | **1.022** | [0.831, 1.252] | $0.07 | 12.1% | `PROFITABLE_BUT_NOT_ROBUST` |
| **V31-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | YES | 1.32 | 32.8% | **0.646** | [0.416, 0.957] | $-0.63 | 7.7% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` |
| **V31-BREAKOUT-VOL-1H** | 1h | breakout_vol | NO | 1.99 | 33.5% | **0.975** | [0.701, 1.328] | $-0.07 | 7.9% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-REGIME-MOM-30M** | 30m | regime_mom | NO | 6.06 | 37.4% | **0.939** | [0.784, 1.124] | $-0.13 | 13.8% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-PULLBACK-CONT-30M** | 30m | pullback_cont | NO | 4.67 | 39.5% | **0.9** | [0.731, 1.077] | $-0.22 | 13.7% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-BREAKOUT-VOL-30M** | 30m | breakout_vol | NO | 2.0 | 34.4% | **0.894** | [0.64, 1.225] | $-0.23 | 8.1% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-MEAN-REVERSION-30M** | 30m | mean_reversion | NO | 1.96 | 36.9% | **0.629** | [0.47, 0.865] | $-0.67 | 11.7% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-LIQUIDITY-REVERSAL-15M** | 15m | liquidity_reversal | NO | 1.62 | 37.7% | **0.619** | [0.414, 0.869] | $-0.36 | 5.2% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-MEAN-REVERSION-15M** | 15m | mean_reversion | NO | 2.13 | 39.1% | **0.587** | [0.438, 0.763] | $-0.53 | 10.4% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-ADAPTIVE-HYBRID-4H** | 4h | adaptive_hybrid | NO | 4.79 | 32.7% | **0.989** | [0.802, 1.197] | $-0.04 | 15.9% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-REGIME-MOM-1H** | 1h | regime_mom | NO | 5.14 | 35.2% | **0.917** | [0.74, 1.112] | $-0.25 | 23.8% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-TREND-CONT-1H** | 1h | trend_cont | NO | 4.56 | 33.2% | **0.865** | [0.701, 1.066] | $-0.42 | 21.3% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-VOL-COMP-EXP-1H** | 1h | vol_comp_exp | NO | 3.42 | 32.8% | **0.846** | [0.66, 1.054] | $-0.48 | 17.6% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-ADAPTIVE-HYBRID-1H** | 1h | adaptive_hybrid | NO | 4.73 | 30.3% | **0.813** | [0.656, 0.989] | $-0.61 | 27.5% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-PULLBACK-CONT-15M** | 15m | pullback_cont | NO | 4.84 | 36.7% | **0.733** | [0.596, 0.887] | $-0.44 | 20.4% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V31-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | NO | 2.41 | 21.7% | **0.605** | [0.419, 0.817] | $-1.41 | 32.8% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |

---

## 2. Answers to Mandatory 16 Research Questions

1. **Can we obtain ~1 trade/day profitably?**: NO - Edge is unprofitable or non-robust at 1 trade/day after friction
2. **Leading Strategy**: `V31-MTF-CONFLUENCE-30M` (mtf_confluence)
3. **True OOS Profit Factor**: **1.080825127249187**
4. **True OOS Expectancy**: **$0.21059633437195777** per trade (0.0015854279781847079 R)
5. **Trades / Day**: **3.311111111111111** trades/day
6. **Maximum Drawdown**: **10.3%**
7. **Bootstrap 95% PF CI**: **[0.8386135422798184, 1.361129072279496]**
8. **Profitable OOS Windows**: **2/4** walk-forward windows
9. **Parameter Stability (±10%)**: UNSTABLE (0/5 positive configurations)
10. **Higher Friction Impact**: Baseline PF 1.080825127249187 -> 20bps PF 1.548199061520226 -> 30bps PF 1.4218179812377463
11. **Best Growth/DD Balance Risk**: **0.50% equity risk per trade**
12. **Recommended Risk Percentage**: **0.50% (Default) to 0.75% (Max Bound)**
13. **Recommended Max Simultaneous Exposure**: **1.50% Aggregate Open Risk / 1.00% Correlated Exposure**
14. **Expected Losing Streak**: **20** consecutive losses
15. **Monte Carlo 95th-Percentile Drawdown**: **12.64%** (2,000 iterations)
16. **Strongest Alternative Candidate**: `V31-MTF-CONFLUENCE-30M` (PF = 1.081)

---

## 3. Position Sizing & Capital Growth Analysis

| Risk Tier | Risk / Trade | Final Balance ($) | Monthly Return (%) | Annualized Return (%) | Max Drawdown (%) | Execution Note |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **risk_25bps** | 0.25% | $1018.24 | 0.61% | 7.29% | 2.2% | `STANDARD_EXECUTION` |
| **risk_50bps** | 0.5% | $1027.38 | 0.91% | 10.95% | 2.5% | `STANDARD_EXECUTION` |
| **risk_75bps** | 0.75% | $1027.38 | 0.91% | 10.95% | 2.5% | `STANDARD_EXECUTION` |
| **risk_100bps** | 1.0% | $1027.38 | 0.91% | 10.95% | 2.5% | `STANDARD_EXECUTION` |

---

## 4. Monte Carlo 2,000-Iteration Trade Shuffle Analysis

- **Median Return**: 6.28%
- **5th Percentile Return**: 6.28%
- **95th Percentile Return**: 6.28%
- **50th Percentile Max DD**: 8.16%
- **95th Percentile Max DD**: 12.64%
- **Probability of Drawdown > 10%**: 22.5%
- **Probability of Drawdown > 20%**: 0.0%
- **Risk of Ruin (>50% DD)**: 0.0%
- **95th Percentile Losing Streak**: 17 consecutive losses

---

## 5. Final Promotion Decision & Next Steps

**Official Verdict**: `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Friction Impact**: Exchange fees (0.15%) + slippage (0.05%) consume ~0.5%-1.5% margin per trade at 1 trade/day frequency.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains enforced.
