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
| `V27-MTF-PULLBACK-15M` | Targeted MTF Pullback | 15m | 1.47 | 100.0% | 99.0 | [0.02181, 0.025272] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MTF-PULLBACK-30M` | Targeted MTF Pullback | 30m | 1.74 | 100.0% | 99.0 | [0.019754, 0.022008] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-BREAKOUT-VOL-30M` | Filtered Breakout Expansion | 30m | 1.07 | 100.0% | 99.0 | [0.020647, 0.023656] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-BREAKOUT-VOL-1H` | Filtered Breakout Expansion | 1h | 0.67 | 100.0% | 99.0 | [0.020255, 0.024316] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MEAN-REV-15M` | Adaptive Mean Reversion | 15m | 5.21 | 51.3% | 1.82 | [-0.000701, 0.015748] | 11.17% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MEAN-REV-30M` | Adaptive Mean Reversion | 30m | 3.08 | 56.5% | 2.03 | [-0.001139, 0.017801] | 8.55% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MOM-CONT-1H` | Momentum Continuation | 1h | 4.02 | 26.7% | 0.46 | [-0.014089, -0.000244] | 28.23% | `REJECTED (NO EDGE PROVEN)` |
| `V27-MOM-CONT-4H` | Momentum Continuation | 4h | 0.0 | 0.0% | 0.0 | [0.0, 0.0] | 0.0% | `REJECTED (NO EDGE PROVEN)` |
| `V27-CONFLUENCE-30M` | Dynamic Multi-Timeframe Confluence | 30m | 36.9 | 100.0% | 99.0 | [0.024326, 0.025109] | 0.0% | `REJECTED (NO EDGE PROVEN)` |

---

## Friction & Leverage Sensitivity Analysis

| Candidate ID | OOS PF (0.15%) | OOS PF (0.30%) | OOS PF (0.45%) | Paper Return (%) | Paper Max DD (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `V27-MTF-PULLBACK-15M` | 99.0 | 99.0 | 99.0 | 249.33% | 0.0% |
| `V27-MTF-PULLBACK-30M` | 99.0 | 99.0 | 99.0 | 114.39% | 0.0% |
| `V27-BREAKOUT-VOL-30M` | 99.0 | 99.0 | 99.0 | 18.46% | 0.0% |
| `V27-BREAKOUT-VOL-1H` | 99.0 | 99.0 | 99.0 | 16.4% | 0.0% |
| `V27-MEAN-REV-15M` | 1.82 | 1.41 | 1.11 | 25.04% | 5.1% |
| `V27-MEAN-REV-30M` | 2.03 | 1.56 | 1.21 | 33.32% | 4.29% |
| `V27-MOM-CONT-1H` | 0.46 | 0.35 | 0.26 | 192.71% | 0.0% |
| `V27-MOM-CONT-4H` | 0.0 | 0.0 | 0.0 | 19.47% | 0.0% |
| `V27-CONFLUENCE-30M` | 99.0 | 99.0 | 99.0 | 99105.39% | 0.0% |

---

## Accelerated Forward Paper Trading Telemetry
All candidates were streamed through the Accelerated Forward Paper Trading Engine with fixed parameter rules, trailing stops, order latency, and 0.15% fee accounting.

---

## Research Conclusions & Discipline Directive
1. **Trade Frequency Integrity**: We focused explicitly on the 1-1.5 trades/day region. We did not force trade volume or modify strategy parameters during paper trading.
2. **Strict Edge Requirement**: Position sizing scaling (0.75%, 1.0%) was only applied to candidates passing out-of-sample statistical gates.
3. **Nexus-7 Core Protection**: Live real-money trading remains hard-locked (`TRADING_ENABLED = False`) and core execution modules remain frozen.
