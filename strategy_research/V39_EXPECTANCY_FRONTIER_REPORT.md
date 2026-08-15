# NEXUS-7 Research V39 — Forensic Real-Market Edge Discovery Report

## Executive Official Verdict: `FRAGILE`

> **System Safety Hard-Lock**: RESEARCH ONLY. LIVE TRADING DISABLED. `TRADING_ENABLED = False`.
> **Data Source Guarantee**: Evaluated on REAL historical mainnet market data (`BINANCE_MAINNET`). Zero synthetic primary evidence.
> **Methodology Guarantee**: Every historical trade outcome was derived exclusively from subsequent bar-by-bar candle traversal.
> Includes 1-bar execution delay, 0.15% round-trip fees, 0.05% slippage per side, and conservative SL/TP same-candle collision handling (treated as LOSS).

---

## Executive Summary Metrics
- **Data Source**: `BINANCE_MAINNET` (Real Historical OHLCV)
- **Best Universe Size**: `TIER_12` (12 eligible assets)
- **Best Strategy**: `V39-PULLBACK-CONT-1H` (pullback_cont)
- **Best Timeframe**: `1h`
- **Trades/Day**: **0.11** trades/day
- **Daily Participation**: **10.0%** of days participating (LOW_PARTICIPATION)
- **Win Rate**: **100.0%**
- **Profit Factor**: **99.0**
- **Bootstrap 95% CI**: `[0.0, 0.0]` (10,000 iterations)
- **Net Expectancy**: **$0.3** per trade
- **Max Drawdown**: **0.0%**
- **Monte Carlo 95% DD**: **0.0%** (10,000 iterations)
- **Walk-Forward**: **0/5** positive windows (0.0%)
- **Parameter Stability**: **77.8%** stability
- **Friction Break-Even Limit**: **30.0 bps**

---

## 1. Candidate Strategies Summary

| Candidate Strategy | Timeframe | Family | Trades/Day | Win Rate (%) | Profit Factor | Bootstrap 95% CI | Net Exp ($) | Max DD (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **V39-TREND-CONT-15M** | 15m | trend_cont | 8.32 | 23.08% | **0.171** | [0.043, 0.498] | $-0.58 | 1.62% | `FRAGILE` |
| **V39-TREND-CONT-1H** | 1h | trend_cont | 0.89 | 37.5% | **0.532** | [0.0, 2.667] | $-0.48 | 0.42% | `FRAGILE` |
| **V39-MOMENTUM-CONT-15M** | 15m | momentum_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V39-MOMENTUM-CONT-1H** | 1h | momentum_cont | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V39-BREAKOUT-15M** | 15m | breakout | 4.16 | 23.08% | **0.122** | [0.0, 0.324] | $-0.67 | 0.88% | `FRAGILE` |
| **V39-BREAKOUT-1H** | 1h | breakout | 0.89 | 25.0% | **0.389** | [0.0, 1.889] | $-0.58 | 0.52% | `FRAGILE` |
| **V39-VOL-BREAKOUT-1H** | 1h | volatility_breakout | 0.89 | 25.0% | **0.368** | [0.0, 1.889] | $-0.6 | 0.52% | `FRAGILE` |
| **V39-MEAN-REVERSION-15M** | 15m | mean_reversion | 3.52 | 18.18% | **0.015** | [0.0, 0.061] | $-0.67 | 0.74% | `FRAGILE` |
| **V39-MEAN-REVERSION-1H** | 1h | mean_reversion | 0.89 | 25.0% | **0.216** | [0.0, 1.146] | $-0.77 | 0.62% | `FRAGILE` |
| **V39-LIQUIDITY-REVERSAL-1H** | 1h | liquidity_reversal | 0.22 | 50.0% | **1.182** | [0.0, 0.0] | $0.15 | 0.17% | `FRAGILE` |
| **V39-PULLBACK-CONT-1H** | 1h | pullback_cont | 0.11 | 100.0% | **99.0** | [0.0, 0.0] | $0.3 | 0.0% | `FRAGILE` |
| **V39-REGIME-TREND-1H** | 1h | regime_trend | 0.89 | 37.5% | **0.532** | [0.0, 2.667] | $-0.48 | 0.42% | `FRAGILE` |
| **V39-REGIME-MEAN-REV-1H** | 1h | regime_mean_rev | 0.89 | 25.0% | **0.216** | [0.0, 1.146] | $-0.77 | 0.62% | `FRAGILE` |
| **V39-VOL-COMPRESSION-1H** | 1h | vol_compression_exp | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V39-MTF-CONFLUENCE-1H** | 1h | mtf_confluence | 0.89 | 37.5% | **0.532** | [0.0, 2.667] | $-0.48 | 0.42% | `FRAGILE` |
| **V39-REL-STRENGTH-1H** | 1h | rel_strength | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V39-CROSS-MOMENTUM-1H** | 1h | cross_momentum | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |
| **V39-CROSS-MEAN-REV-1H** | 1h | cross_mean_rev | 0.89 | 25.0% | **0.216** | [0.0, 1.146] | $-0.77 | 0.62% | `FRAGILE` |
| **V39-MARKET-NEUTRAL-1H** | 1h | market_neutral_rv | 0.89 | 25.0% | **0.216** | [0.0, 1.146] | $-0.77 | 0.62% | `FRAGILE` |
| **V39-BASIS-FUNDING-1H** | 1h | basis_funding | 0.89 | 37.5% | **0.532** | [0.0, 2.667] | $-0.48 | 0.42% | `FRAGILE` |
| **V39-FLOW-CONFIRMATION-1H** | 1h | flow_confirmation | 0.22 | 50.0% | **1.182** | [0.0, 0.0] | $0.15 | 0.17% | `FRAGILE` |
| **V39-BTC-ALT-REGIME-1H** | 1h | btc_altcoin_regime | 0.0 | 0.0% | **0.0** | [0.0, 0.0] | $0.0 | 0.0% | `FRAGILE` |

---

## 2. Frequency Frontier Bands Summary

| Frequency Band | Best Strategy | Trades/Day | Profit Factor | Net Exp ($) | Max DD (%) | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **0.25_TRADES_DAY** | V39-PULLBACK-CONT-1H | 0.11 | **99.0** | $0.3 | 0.0% | `FRAGILE` |
| **0.50_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **0.75_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **1.00_TRADES_DAY** | V39-TREND-CONT-1H | 0.89 | **0.532** | $-0.48 | 0.42% | `FRAGILE` |
| **1.50_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **2.00_TRADES_DAY** | NONE | 0.0 | **0.0** | $0.0 | 0.0% | `NO_ROBUST_EDGE_FOUND` |
| **3.00_TRADES_DAY** | V39-MEAN-REVERSION-15M | 3.52 | **0.015** | $-0.67 | 0.74% | `FRAGILE` |
| **5.00_PLUS_TRADES_DAY** | V39-TREND-CONT-15M | 8.32 | **0.171** | $-0.58 | 1.62% | `FRAGILE` |

---

## 3. Final Promotion Decision & System Status

**Official Verdict**: `FRAGILE`

1. **Zero-Stub Forensic Integrity**: Verified bar-by-bar candle traversal eliminates synthetic artifact spikes.
2. **Real Market Evidence**: Real market data audit completed (`V39_DATA_INTEGRITY_REPORT.md`).
3. **State of System**: `TRADING_ENABLED = False` hard-lock remains strictly enforced.
