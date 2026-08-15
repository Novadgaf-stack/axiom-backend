# NEXUS-7 Research V29 — Zero-Stub Forensic Expectancy Search & Frontier Report

## Executive Overall Verdict: `NO ROBUST PROFITABLE EDGE FOUND`

> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## 1. Frequency vs Expectancy vs Drawdown Frontier Table (Untouched OOS)

| Candidate Strategy | Timeframe | Target Window (0.8-1.8/d) | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp / Trade ($) | Max Drawdown (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V28-BREAKOUT-VOL-30M** | 30m | NO | 2.37 | 36.6% | **0.883** | [0.655, 1.167] | $-0.26 | 10.8% | `FAIL_EXPECTANCY` |
| **V28-BREAKOUT-VOL-1H** | 1h | NO | 2.03 | 37.2% | **1.021** | [0.74, 1.368] | $0.06 | 8.5% | `FAIL_PF_CI_GATE` |
| **V28-MTF-PULLBACK-15M** | 15m | NO | 5.69 | 38.3% | **0.809** | [0.673, 0.968] | $-0.34 | 20.0% | `FAIL_EXPECTANCY` |
| **V28-MTF-PULLBACK-30M** | 30m | NO | 5.81 | 34.8% | **0.782** | [0.652, 0.949] | $-0.56 | 31.5% | `FAIL_EXPECTANCY` |
| **V28-REGIME-REVERSION-15M** | 15m | NO | 2.4 | 44.0% | **0.721** | [0.551, 0.931] | $-0.33 | 7.6% | `FAIL_EXPECTANCY` |
| **V28-REGIME-REVERSION-30M** | 30m | NO | 2.57 | 42.0% | **0.783** | [0.599, 1.008] | $-0.36 | 9.7% | `FAIL_EXPECTANCY` |
| **V28-MOM-CONTINUATION-30M** | 30m | NO | 2.81 | 33.6% | **0.906** | [0.689, 1.195] | $-0.23 | 10.7% | `FAIL_EXPECTANCY` |
| **V28-MOM-CONTINUATION-1H** | 1h | NO | 2.98 | 32.5% | **0.895** | [0.672, 1.158] | $-0.35 | 18.0% | `FAIL_EXPECTANCY` |
| **V28-DYNAMIC-CONFLUENCE-1H** | 1h | NO | 5.87 | 29.5% | **0.927** | [0.767, 1.131] | $-0.27 | 21.8% | `FAIL_EXPECTANCY` |
| **V28-DYNAMIC-CONFLUENCE-4H** | 4h | NO | 6.04 | 29.4% | **0.963** | [0.799, 1.142] | $-0.14 | 15.4% | `FAIL_EXPECTANCY` |
| **V29-LIQUIDITY-SWEEP-15M** | 15m | YES | 1.38 | 32.3% | **0.422** | [0.274, 0.633] | $-0.6 | 7.6% | `FAIL_EXPECTANCY` |
| **V29-LIQUIDITY-SWEEP-1H** | 1h | YES | 1.68 | 29.1% | **0.535** | [0.363, 0.791] | $-0.93 | 14.2% | `FAIL_EXPECTANCY` |

---

## 2. Best-in-Class Strategy Identifications

- **BEST PROFITABLE CANDIDATE**: `V28-BREAKOUT-VOL-1H` (PF = 1.021, Net Exp = $0.06)
- **BEST FREQUENCY CANDIDATE**: `V29-LIQUIDITY-SWEEP-1H` (1.68 trades/day, PF = 0.535)
- **BEST RISK-ADJUSTED CANDIDATE**: `V28-BREAKOUT-VOL-1H` (Return/DD = 0.001)
- **BEST ROBUST CANDIDATE**: `V28-DYNAMIC-CONFLUENCE-4H` (CI Lower Bound = 0.799)

---

## 3. Position Sizing & Multi-Friction Sensitivity Analysis

### Risk Budget Sizing Tiers (Evaluated at 0.15% fee, 0.05% slippage):
- **0.25% Account Risk**: Baseline conservative risk tier. Bounded drawdown.
- **0.50% Account Risk**: Default research risk budget.
- **0.75% Account Risk**: High-confidence setup upper bound.
- **1.00% Account Risk**: Research sensitivity case.

> [!IMPORTANT]
> **Dynamic Sizing Principle**: When underlying edge is negative ($	ext{PF} < 1.00$), increasing position risk budget merely magnifies capital loss. Staking higher does NOT manufacture profitability.

---

## 4. Key Scientific Conclusions & Next Steps

1. **Forensic Integrity Validated**: Zero-stub candle traversal eliminates all synthetic artifact spikes ($PF=99$).
2. **Friction Drag Impact**: At 1.0-1.5 trades/day frequency, transaction costs (0.15% fees + 0.05% slippage) consume ~0.5%-1.5% of nominal margin per trade.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains enforced. All candidates require forward paper validation prior to live consideration.
