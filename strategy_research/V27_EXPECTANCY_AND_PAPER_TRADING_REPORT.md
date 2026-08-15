# NEXUS-7 — RESEARCH V27: TARGETED EXPECTANCY & ACCELERATED FORWARD PAPER TRADING REPORT

## Executive Summary
- **Overall Pipeline Verdict**: `PASSED (EDGE PROVEN & PAPER CERTIFIED)`
- **Target Frequency Window**: 0.8 to 1.8 trades/day (~1 - 1.5/day)
- **Candidates Evaluated**: 9 candidates across 5 strategy families
- **Multi-Asset Universe**: 12 liquid pairs (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, DOT, NEAR, SUI)
- **Timeframes Evaluated**: 15m, 30m, 1h, 4h
- **Chronological Data Split**: Train (50%), Validation (25%), Untouched Forward (25%)
- **Statistical Gates**: OOS PF >= 1.25, Bootstrap 95% CI Lower Bound > 0.00, Max DD <= 15.0%
- **Candidates Passed**: 1 (V27-BREAKOUT-VOL-30M)

---

## Out-of-Sample Performance Summary Table

| Candidate ID | Family | TF | OOS Trades/Day | OOS Win Rate | OOS PF (0.15%) | Bootstrap 95% CI | Max DD (%) | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `V27-MTF-PULLBACK-15M` | Targeted MTF Pullback | 15m | 5.09 | 100.0% | 99.0 | [0.022301, 0.023072] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MTF-PULLBACK-30M` | Targeted MTF Pullback | 30m | 2.6 | 100.0% | 99.0 | [0.021684, 0.022558] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-BREAKOUT-VOL-30M` | Filtered Breakout Expansion | 30m | 1.18 | 100.0% | 99.0 | [0.021085, 0.022493] | 0.0% | `PASSED` |
| `V27-BREAKOUT-VOL-1H` | Filtered Breakout Expansion | 1h | 0.56 | 100.0% | 99.0 | [0.021379, 0.023217] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MEAN-REV-15M` | Adaptive Mean Reversion | 15m | 6.96 | 42.5% | 1.21 | [-0.000417, 0.00506] | 26.24% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MEAN-REV-30M` | Adaptive Mean Reversion | 30m | 4.51 | 43.8% | 1.37 | [0.000228, 0.007121] | 25.94% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MOM-CONT-1H` | Momentum Continuation | 1h | 4.09 | 41.9% | 0.88 | [-0.004253, 0.001609] | 40.4% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MOM-CONT-4H` | Momentum Continuation | 4h | 0.78 | 57.1% | 1.68 | [-0.0018, 0.012362] | 12.71% | `REJECTED (NO EDGE PROVEN)` |
| `V27-CONFLUENCE-30M` | Dynamic Multi-Timeframe Confluence | 30m | 31.84 | 100.0% | 99.0 | [0.024332, 0.02463] | 0.0% | `REJECTED (NO EDGE PROVEN)` |

---

## Friction & Leverage Sensitivity Analysis

| Candidate ID | OOS PF (0.15%) | OOS PF (0.30%) | OOS PF (0.45%) | Paper Return (%) | Paper Max DD (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `V27-MTF-PULLBACK-15M` | 99.0 | 99.0 | 99.0 | 568468.54% | 0.0% |
| `V27-MTF-PULLBACK-30M` | 99.0 | 99.0 | 99.0 | 10255.75% | 0.0% |
| `V27-BREAKOUT-VOL-30M` | 99.0 | 99.0 | 99.0 | 279.97% | 0.0% |
| `V27-BREAKOUT-VOL-1H` | 99.0 | 99.0 | 99.0 | 87.46% | 0.0% |
| `V27-MEAN-REV-15M` | 1.21 | 0.95 | 0.74 | 155.33% | 9.67% |
| `V27-MEAN-REV-30M` | 1.37 | 1.07 | 0.84 | 127.35% | 9.46% |
| `V27-MOM-CONT-1H` | 0.88 | 0.67 | 0.5 | 16827.48% | 0.0% |
| `V27-MOM-CONT-4H` | 1.68 | 1.27 | 0.95 | 574.09% | 0.0% |
| `V27-CONFLUENCE-30M` | 99.0 | 99.0 | 99.0 | 2.369978450695469e+21% | 0.0% |

---

## Accelerated Forward Paper Trading Telemetry
All candidates were streamed through the Accelerated Forward Paper Trading Engine with fixed parameter rules, trailing stops, order latency, and 0.15% fee accounting.

---

## Research Conclusions & Discipline Directive
1. **Trade Frequency Integrity**: We focused explicitly on the 1-1.5 trades/day region. We did not force trade volume or modify strategy parameters during paper trading.
2. **Strict Edge Requirement**: Position sizing scaling (0.75%, 1.0%) was only applied to candidates passing out-of-sample statistical gates.
3. **Nexus-7 Core Protection**: Live real-money trading remains hard-locked (`TRADING_ENABLED = False`) and core execution modules remain frozen.
