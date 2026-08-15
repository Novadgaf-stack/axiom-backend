# NEXUS-7 Research V30 — Robust ~1 Trade/Day Profitability Research Report

## Executive Official Verdict: `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## 1. Frequency vs Expectancy vs Drawdown Frontier Table (Untouched OOS)

| Candidate Strategy | Timeframe | Family | Target Window (0.75-1.50/d) | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp / Trade ($) | Max Drawdown (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V30-VOL-ADAPTIVE-4H** | 4h | vol_adaptive | NO | 4.23 | 36.2% | **1.04** | [0.849, 1.273] | $0.13 | 10.8% | `PROFITABLE_BUT_NOT_ROBUST` |
| **V30-STRUCTURE-SWEEP-30M** | 30m | liquidity_reversal | YES | 1.4 | 40.5% | **0.878** | [0.589, 1.264] | $-0.15 | 4.6% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` |
| **V30-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | YES | 1.34 | 32.2% | **0.629** | [0.401, 0.929] | $-0.68 | 8.3% | `FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE` |
| **V30-REGIME-TREND-30M** | 30m | regime_trend | NO | 4.94 | 38.7% | **0.978** | [0.796, 1.179] | $-0.05 | 11.3% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-BREAKOUT-VOL-1H** | 1h | breakout_vol | NO | 2.09 | 33.0% | **0.924** | [0.656, 1.247] | $-0.24 | 10.0% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-BREAKOUT-VOL-30M** | 30m | breakout_vol | NO | 2.16 | 33.5% | **0.844** | [0.604, 1.136] | $-0.35 | 10.7% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-LIQUIDITY-REVERSAL-15M** | 15m | liquidity_reversal | NO | 1.62 | 37.7% | **0.619** | [0.414, 0.869] | $-0.36 | 5.2% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-MTF-CONFLUENCE-30M** | 30m | mtf_confluence | NO | 5.42 | 32.8% | **0.985** | [0.801, 1.208] | $-0.04 | 17.5% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-VOL-ADAPTIVE-1H** | 1h | vol_adaptive | NO | 4.08 | 34.6% | **0.902** | [0.722, 1.123] | $-0.31 | 18.7% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-REGIME-TREND-1H** | 1h | regime_trend | NO | 5.03 | 34.9% | **0.89** | [0.723, 1.072] | $-0.35 | 27.4% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-HYBRID-REGIME-1H** | 1h | regime_trend | NO | 5.03 | 34.9% | **0.89** | [0.723, 1.072] | $-0.35 | 27.4% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-PULLBACK-CONT-30M** | 30m | pullback_cont | NO | 4.93 | 38.7% | **0.883** | [0.715, 1.065] | $-0.26 | 16.1% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | NO | 5.41 | 27.5% | **0.807** | [0.658, 0.984] | $-0.71 | 35.0% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |
| **V30-PULLBACK-CONT-15M** | 15m | pullback_cont | NO | 5.26 | 37.6% | **0.756** | [0.621, 0.899] | $-0.4 | 20.0% | `NO_ROBUST_PROFITABLE_EDGE_FOUND` |

---

## 2. Best-in-Class Strategy Identifications

- **BEST PROFITABLE CANDIDATE**: `V30-VOL-ADAPTIVE-4H` (PF = 1.04, Net Exp = $0.13)
- **BEST FREQUENCY CANDIDATE**: `V30-STRUCTURE-SWEEP-30M` (1.4 trades/day, PF = 0.878)
- **BEST RISK-ADJUSTED CANDIDATE**: `V30-VOL-ADAPTIVE-4H` (Return/DD = 0.001)
- **BEST ROBUST CANDIDATE**: `V30-VOL-ADAPTIVE-4H` (CI Lower Bound = 0.849)

---

## 3. Position Sizing & Monte Carlo Risk Research

### Position Risk Budgets Evaluated:
- **0.25% Account Risk**: Baseline conservative risk tier.
- **0.50% Account Risk**: Reference research risk budget.
- **0.75% Account Risk**: High-confidence setup upper bound.
- **1.00% Account Risk**: Sensitivity research case.

> [!IMPORTANT]
> **Position Sizing Rule Enforced**: If Profit Factor <= 1.00 or Net Expectancy <= 0, position size MUST NOT be increased. Staking higher does NOT manufacture profitability on a negative-expectancy strategy.

### Monte Carlo 1,000-Iteration Trade Shuffle Results (Leading Candidate):
- **Median Simulated Return**: 5.12%
- **Worst-Case Return**: 5.12%
- **Drawdown 5th Percentile**: 8.19%
- **Drawdown 50th Percentile**: 11.88%
- **Drawdown 95th Percentile**: 18.3%
- **Probability of Drawdown > 10%**: 77.3%
- **Probability of Drawdown > 20%**: 2.2%
- **Probability of Negative Return**: 0.0%
- **95th Percentile Losing Streak**: 17 consecutive losses

---

## 4. Robustness & Walk-Forward Validation Results

- **Chronological Walk-Forward Consistency**: 50.0% (2/4 positive OOS windows)
- **Neighboring Parameter Stability (±10%)**: UNSTABLE (2/3 positive parameter configurations)

---

## 5. Key Scientific Conclusions & Next Steps

1. **Forensic Integrity Validated**: Zero-stub bar-by-bar candle traversal eliminates all synthetic artifact spikes.
2. **Friction Drag Impact**: In the 0.75-1.50 trades/day frequency target, friction (0.15% fee + 0.05% slippage) eats ~0.5%-1.5% nominal margin per trade.
3. **System Safety**: `TRADING_ENABLED = False` hard-lock remains active. Live trading is strictly disabled.
