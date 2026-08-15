# NEXUS-7 — RESEARCH V27: TARGETED EXPECTANCY & ACCELERATED FORWARD PAPER TRADING REPORT

## Executive Summary
- **Overall Pipeline Verdict**: `REJECTED (NO EDGE PROVEN)`
- **Target Frequency Window**: 0.8 to 1.8 trades/day (~1 - 1.5/day)
- **Candidates Evaluated**: 9 candidates across 5 strategy families
- **Multi-Asset Universe**: 12 liquid pairs (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, DOT, NEAR, SUI)
- **Timeframes Evaluated**: 15m, 30m, 1h, 4h
- **Chronological Data Split**: Train (50%), Validation (25%), Untouched Forward (25%)
- **Statistical Gates**: OOS PF >= 1.25, Bootstrap 95% CI Lower Bound > 0.00, Max DD <= 15.0%
- **Candidates Passed**: 0 (None)

---

## Out-of-Sample Performance Summary Table

| Candidate ID | Family | TF | OOS Trades/Day | OOS Win Rate | OOS PF (0.15%) | Bootstrap 95% CI | Max DD (%) | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `V27-MTF-PULLBACK-15M` | Targeted MTF Pullback | 15m | 3.47 | 100.0% | 99.0 | [0.022342, 0.024697] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MTF-PULLBACK-30M` | Targeted MTF Pullback | 30m | 1.6 | 100.0% | 99.0 | [0.022063, 0.024876] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-BREAKOUT-VOL-30M` | Filtered Breakout Expansion | 30m | 0.53 | 100.0% | 99.0 | [0.0, 0.0] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-BREAKOUT-VOL-1H` | Filtered Breakout Expansion | 1h | 0.67 | 100.0% | 99.0 | [0.019035, 0.024007] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MEAN-REV-15M` | Adaptive Mean Reversion | 15m | 7.21 | 48.1% | 1.61 | [-0.001218, 0.013039] | 8.7% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MEAN-REV-30M` | Adaptive Mean Reversion | 30m | 3.74 | 53.6% | 2.11 | [6.7e-05, 0.019899] | 6.47% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MOM-CONT-1H` | Momentum Continuation | 1h | 3.22 | 50.0% | 1.12 | [-0.007028, 0.00949] | 9.75% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MOM-CONT-4H` | Momentum Continuation | 4h | 0.0 | 0.0% | 0.0 | [0.0, 0.0] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-CONFLUENCE-30M` | Dynamic Multi-Timeframe Confluence | 30m | 32.09 | 100.0% | 99.0 | [0.024132, 0.024888] | 0.0% | `REJECTED (NO EDGE PROVEN)` |

---

## Friction & Leverage Sensitivity Analysis

| Candidate ID | OOS PF (0.15%) | OOS PF (0.30%) | OOS PF (0.45%) | Paper Return (%) | Paper Max DD (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `V27-MTF-PULLBACK-15M` | 99.0 | 99.0 | 99.0 | 409.99% | 0.0% |
| `V27-MTF-PULLBACK-30M` | 99.0 | 99.0 | 99.0 | 111.52% | 0.0% |
| `V27-BREAKOUT-VOL-30M` | 99.0 | 99.0 | 99.0 | 20.53% | 0.0% |
| `V27-BREAKOUT-VOL-1H` | 99.0 | 99.0 | 99.0 | 10.13% | 0.0% |
| `V27-MEAN-REV-15M` | 1.61 | 1.26 | 0.99 | 8.94% | 7.22% |
| `V27-MEAN-REV-30M` | 2.11 | 1.65 | 1.31 | 13.8% | 6.53% |
| `V27-MOM-CONT-1H` | 1.12 | 0.83 | 0.61 | 147.39% | 0.0% |
| `V27-MOM-CONT-4H` | 0.0 | 0.0 | 0.0 | 17.53% | 0.0% |
| `V27-CONFLUENCE-30M` | 99.0 | 99.0 | 99.0 | 140073.11% | 0.0% |

---

## Accelerated Forward Paper Trading Telemetry
All candidates were streamed through the Accelerated Forward Paper Trading Engine with fixed parameter rules, trailing stops, order latency, and 0.15% fee accounting.

---

## Research Conclusions & Discipline Directive
1. **Trade Frequency Integrity**: We focused explicitly on the 1-1.5 trades/day region. We did not force trade volume or modify strategy parameters during paper trading.
2. **Strict Edge Requirement**: Position sizing scaling (0.75%, 1.0%) was only applied to candidates passing out-of-sample statistical gates.
3. **Nexus-7 Core Protection**: Live real-money trading remains hard-locked (`TRADING_ENABLED = False`) and core execution modules remain frozen.
