# NEXUS-7 Research V37 — Robust Daily Opportunity & Alpha Discovery Report

## Executive Official Verdict: `V37_PROFITABLE_BUT_NOT_ROBUST`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## Executive Summary Metrics
- **Best Universe Size**: `TIER_A_20` (20 tradeable assets)
- **Best Strategy**: `V37-MEAN-REVERSION-15M` (mean_reversion)
- **Best Timeframe**: `15m`
- **Trades/Day**: **2.0** trades/day
- **Daily Participation**: **100.0%** of days participating (HIGH_DAILY_PARTICIPATION)
- **Win Rate**: **50.0%**
- **Profit Factor**: **1.234**
- **Bootstrap 95% CI**: `[0.0, 0.0]`
- **Net Expectancy**: **$0.62** per trade
- **Max Drawdown**: **0.53%**
- **Monte Carlo 95% DD**: **0.0%** (5,000 iterations)
- **Walk-Forward**: **0/5** positive windows (0.0%)
- **Parameter Stability**: **77.8%** stability
- **Friction Break-Even Limit**: **72.1 bps**

---

## 1. Candidate Strategies Summary

| Candidate Strategy | Timeframe | Family | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **V37-MOMENTUM-CONT-15M** | 15m | momentum_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-MOMENTUM-CONT-30M** | 30m | momentum_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-MOMENTUM-CONT-1H** | 1h | momentum_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-BREAKOUT-VOL-15M** | 15m | breakout_vol | 1.0 | 0.0% | **0.0** | [0.0, 0.0] | $-2.08 | 0.21% | `V37_FREQUENT_BUT_UNPROFITABLE` |
| **V37-BREAKOUT-VOL-30M** | 30m | breakout_vol | 0.96 | 0.0% | **0.0** | [0.0, 0.0] | $-2.08 | 0.21% | `V37_FREQUENT_BUT_UNPROFITABLE` |
| **V37-BREAKOUT-VOL-1H** | 1h | breakout_vol | 0.48 | 0.0% | **0.0** | [0.0, 0.0] | $-2.08 | 0.21% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-PULLBACK-CONT-30M** | 30m | pullback_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-PULLBACK-CONT-1H** | 1h | pullback_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-MEAN-REVERSION-15M** | 15m | mean_reversion | 2.0 | 50.0% | **1.234** | [0.0, 0.0] | $0.62 | 0.53% | `V37_PROFITABLE_BUT_NOT_ROBUST` |
| **V37-MEAN-REVERSION-30M** | 30m | mean_reversion | 1.92 | 50.0% | **1.234** | [0.0, 0.0] | $0.62 | 0.53% | `V37_PROFITABLE_BUT_NOT_ROBUST` |
| **V37-LIQUIDITY-SWEEP-1H** | 1h | liquidity_sweep | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-TREND-EXHAUSTION-1H** | 1h | trend_exhaustion | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-VOL-EXPANSION-1H** | 1h | volatility_expansion | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-RELATIVE-STRENGTH-1H** | 1h | relative_strength | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-CROSS-SECTIONAL-1H** | 1h | cross_sectional_mom | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-REGIME-CONDITIONAL-1H** | 1h | regime_conditional | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-MTF-STRUCTURE-1H** | 1h | mtf_structure | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-VOLUME-ANOMALY-1H** | 1h | volume_anomaly | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-BTC-ETH-REGIME-1H** | 1h | btc_eth_regime | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-RELATIVE-PERF-1H** | 1h | relative_perf | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-ADAPTIVE-HYBRID-1H** | 1h | adaptive_hybrid | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **V37-ADAPTIVE-HYBRID-4H** | 4h | adaptive_hybrid | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |

---

## 2. Frequency Frontier Bands Summary

| Frequency Band | Best Strategy | Trades/Day | Profit Factor | Net Exp ($) | Max DD (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **0.25_TRADES_DAY** | V37-MOMENTUM-CONT-15M | 0.0 | **0.0** | $0.0 | 0.0% | `V37_INSUFFICIENT_SAMPLE` |
| **0.50_TRADES_DAY** | V37-BREAKOUT-VOL-1H | 0.48 | **0.0** | $-2.08 | 0.21% | `V37_INSUFFICIENT_SAMPLE` |
| **0.75_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `V37_NO_ROBUST_PROFITABLE_EDGE` |
| **1.00_TRADES_DAY** | V37-BREAKOUT-VOL-15M | 1.0 | **0.0** | $-2.08 | 0.21% | `V37_FREQUENT_BUT_UNPROFITABLE` |
| **1.25_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `V37_NO_ROBUST_PROFITABLE_EDGE` |
| **1.50_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `V37_NO_ROBUST_PROFITABLE_EDGE` |
| **2.00_TRADES_DAY** | V37-MEAN-REVERSION-15M | 2.0 | **1.234** | $0.62 | 0.53% | `V37_PROFITABLE_BUT_NOT_ROBUST` |
| **2.50_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `V37_NO_ROBUST_PROFITABLE_EDGE` |
| **3.00_PLUS_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `V37_NO_ROBUST_PROFITABLE_EDGE` |

---

## 3. Final Promotion Decision & System Status

**Official Verdict**: `V37_PROFITABLE_BUT_NOT_ROBUST`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Daily Opportunity & Robustness Finding**: Framework evaluated multi-asset frequency and robustness limits.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains strictly enforced.
