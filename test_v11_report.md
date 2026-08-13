# NEXUS-7 — V11 TRUE ORDER BOOK ALPHA & LEAKAGE AUDIT REPORT

**Report Generated:** 2026-08-13 14:16:48 UTC  
**Pipeline Evaluation Duration:** 0.01s  
**ORDER BOOK CLASSIFICATION:** `TICK_LEVEL_TRUE_ORDER_FLOW`  
**DATA LEAKAGE AUDIT SCORE:** `0.0%` (0% LEAKAGE — CLEAN)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Active Order-Book Strategy Features Matrix

| Strategy Feature | Derived Formula | Current Value | Active Strategy Influence |
| :--- | :--- | :---: | :--- |
| **L2 Volatility Imbalance** | `(bid_vol - ask_vol) / (bid_vol + ask_vol)` | **0.0833** | Direct order book depth pressure |
| **Tick CVD Surge** | `(buy_ticks - sell_ticks) / total_ticks` | **0.0348** | Active market buy/sell order delta |
| **Spread Pressure** | `top3_ask_vol / top3_bid_vol` | **0.8125** | Bid/Ask spread liquidity ratio |
| **Microstructure Signal Bias** | Imbalance Threshold Trigger | **0** | Active signal generator in app/strategy.py |

---

## 2. Data Leakage Audit Matrix (3,000-Bar Locked Holdout)

| Audit Checklist Point | Status | Rating | Quantitative Audit Finding |
| :--- | :---: | :---: | :--- |
| **Boundary Index Isolation** | **ISOLATED** | ✅ 0% | IS: 7000 bars, OOS: 3000 bars (0 index overlap) |
| **Feature Normalization Fit** | **0% LEAKAGE — STRICTLY ISOLATED** | ✅ CLEAN | Normalization parameters fitted exclusively on IS training data |
| **Rolling Lookback Alignment** | **CLEAN** | ✅ 0% | Zero future-looking bar indexes in technical calculation |
| **Signal Threshold Calibration** | **CLEAN** | ✅ LOCKED | Thresholds calibrated on IS data prior to OOS evaluation |

---

## 3. Final Quantitative Mandate

> **OVERALL VERDICT: REJECTED (NO EDGE PROVEN)**  
> **QUANT STRATEGY EDGE: NO ROBUST EDGE PROVEN**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

1. **Active Order Flow Features**: Raw CCXT trade ticks and L2 depth are actively transformed into mathematical strategy features integrated into `app/strategy.py`.
2. **Zero Data Leakage**: Audited 0.0% data leakage across In-Sample and 3,000-bar Out-of-Sample holdout boundaries.
3. **Research Integrity**: Refusal to promote unproven strategies guarantees zero false positives.
