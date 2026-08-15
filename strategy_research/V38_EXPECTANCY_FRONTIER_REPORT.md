# NEXUS-7 Research V38 — Robust Multi-Asset Quantitative Research Report

## Executive Official Verdict: `FRAGILE`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).
> Anti-stub unit tests prove outcome cannot be spoofed by confidence scores or candidate IDs.

---

## Executive Summary Metrics
- **Best Universe Size**: `TIER_20` (20 tradeable assets)
- **Best Strategy**: `V38-MEAN-REVERSION-15M` (mean_reversion)
- **Best Timeframe**: `15m`
- **Trades/Day**: **1.0** trades/day
- **Daily Participation**: **100.0%** of days participating (HIGH_DAILY_PARTICIPATION)
- **Win Rate**: **100.0%**
- **Profit Factor**: **99.0**
- **Bootstrap 95% CI**: `[0.0, 0.0]` (10,000 iterations)
- **Net Expectancy**: **$3.27** per trade
- **Max Drawdown**: **0.0%**
- **Monte Carlo 95% DD**: **0.0%** (10,000 iterations)
- **Walk-Forward**: **0/5** positive windows (0.0%)
- **Parameter Stability**: **100.0%** stability
- **Friction Break-Even Limit**: **99.9 bps**

---

## 1. Candidate Strategies Summary

| Candidate Strategy | Timeframe | Family | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **V38-TREND-CONT-15M** | 15m | trend_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-TREND-CONT-1H** | 1h | trend_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-MOMENTUM-CONT-15M** | 15m | momentum_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-MOMENTUM-CONT-1H** | 1h | momentum_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-BREAKOUT-15M** | 15m | breakout | 1.0 | 0.0% | **0.0** | [0.0, 0.0] | $-5.19 | 0.52% | `FRAGILE` |
| **V38-BREAKOUT-1H** | 1h | breakout | 0.53 | 0.0% | **0.0** | [0.0, 0.0] | $-5.19 | 0.52% | `FRAGILE` |
| **V38-VOL-BREAKOUT-1H** | 1h | volatility_breakout | 0.53 | 0.0% | **0.0** | [0.0, 0.0] | $-2.11 | 0.21% | `FRAGILE` |
| **V38-MEAN-REVERSION-15M** | 15m | mean_reversion | 1.0 | 100.0% | **99.0** | [0.0, 0.0] | $3.27 | 0.0% | `FRAGILE` |
| **V38-MEAN-REVERSION-1H** | 1h | mean_reversion | 0.53 | 100.0% | **99.0** | [0.0, 0.0] | $3.27 | 0.0% | `FRAGILE` |
| **V38-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-PULLBACK-CONT-1H** | 1h | pullback_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-REGIME-TREND-1H** | 1h | regime_trend | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-REGIME-MEAN-REV-1H** | 1h | regime_mean_rev | 0.53 | 100.0% | **99.0** | [0.0, 0.0] | $3.27 | 0.0% | `FRAGILE` |
| **V38-VOL-COMPRESSION-1H** | 1h | vol_compression_exp | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-REL-STRENGTH-1H** | 1h | rel_strength | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-CROSS-MOMENTUM-1H** | 1h | cross_momentum | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-CROSS-MEAN-REV-1H** | 1h | cross_mean_rev | 0.53 | 100.0% | **99.0** | [0.0, 0.0] | $3.27 | 0.0% | `FRAGILE` |
| **V38-MARKET-NEUTRAL-1H** | 1h | market_neutral_rv | 0.53 | 100.0% | **99.0** | [0.0, 0.0] | $3.27 | 0.0% | `FRAGILE` |
| **V38-BASIS-FUNDING-1H** | 1h | basis_funding | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-FLOW-CONFIRMATION-1H** | 1h | flow_confirmation | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V38-BTC-ALT-REGIME-1H** | 1h | btc_altcoin_regime | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |

---

## 2. Frequency Frontier Bands Summary

| Frequency Band | Best Strategy | Trades/Day | Profit Factor | Net Exp ($) | Max DD (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **0.25_TRADES_DAY** | V38-TREND-CONT-15M | 0.0 | **0.0** | $0.0 | 0.0% | `FRAGILE` |
| **0.50_TRADES_DAY** | V38-MEAN-REVERSION-1H | 0.53 | **99.0** | $3.27 | 0.0% | `FRAGILE` |
| **0.75_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **1.00_TRADES_DAY** | V38-MEAN-REVERSION-15M | 1.0 | **99.0** | $3.27 | 0.0% | `FRAGILE` |
| **1.25_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **1.50_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **2.00_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **2.50_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **3.00_PLUS_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |

---

## 3. Final Promotion Decision & System Status

**Official Verdict**: `FRAGILE`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Daily Opportunity & Robustness Finding**: Framework evaluated multi-asset frequency, multiple testing, and robustness limits.
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains strictly enforced.
