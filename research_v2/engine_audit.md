# NEXUS-7 — RESEARCH ENGINE AUDIT REPORT (PHASE 0)

**Audit Generated:** 2026-08-11 11:31:14 UTC | **Runtime:** 0.14s  
**Engine Uniqueness Verdict:** `PASSED — ALL SIGNALS INDEPENDENT`

---

## 1. Strategy Signal Fingerprint Matrix

| Exp ID | Strategy Family Name | Total Signals | Unique Timestamps | Long Signals | Short Signals |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **EXP-V2-01** | Strategy A — Time-Series Momentum | 176 | 176 | 176 | 0 |
| **EXP-V2-02** | Strategy B — Cross-Sectional Relative Strength | 1760 | 1760 | 1760 | 0 |
| **EXP-V2-03** | Strategy C — Volatility Breakout | 258 | 258 | 258 | 0 |
| **EXP-V2-04** | Strategy D — Statistical Z-Score Mean Reversion | 25 | 25 | 25 | 0 |
| **EXP-V2-05** | Strategy E — Cross-Asset Lead/Lag Predictive Model | 151 | 151 | 151 | 0 |
| **EXP-V2-06** | Strategy F — Market-Neutral Relative Value Spread | 0 | 0 | 0 | 0 |
| **EXP-V2-07** | Strategy G — Cost-Aware Expected Return Gate | 356 | 356 | 356 | 0 |

---

## 2. Pairwise Signal Overlap Matrix (% Jaccard Similarity)

| Exp ID | EXP-V2-01 | EXP-V2-02 | EXP-V2-03 | EXP-V2-04 | EXP-V2-05 | EXP-V2-06 | EXP-V2-07 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-V2-01** | 100.0% | 5.8% | 9.3% | 0.0% | 5.8% | 0.0% | 39.6% |
| **EXP-V2-02** | 5.8% | 100.0% | 6.5% | 0.0% | 3.9% | 0.0% | 8.7% |
| **EXP-V2-03** | 9.3% | 6.5% | 100.0% | 0.0% | 3.0% | 0.0% | 13.1% |
| **EXP-V2-04** | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| **EXP-V2-05** | 5.8% | 3.9% | 3.0% | 0.0% | 100.0% | 0.0% | 12.7% |
| **EXP-V2-06** | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| **EXP-V2-07** | 39.6% | 8.7% | 13.1% | 0.0% | 12.7% | 0.0% | 100.0% |

---

## 3. Mathematical Uniqueness Assertions

- [PASS] EXP-V2-01 vs EXP-V2-02: Overlap = 5.79% (Independent)
- [PASS] EXP-V2-01 vs EXP-V2-03: Overlap = 9.32% (Independent)
- [PASS] EXP-V2-01 vs EXP-V2-04: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-01 vs EXP-V2-05: Overlap = 5.83% (Independent)
- [PASS] EXP-V2-01 vs EXP-V2-06: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-01 vs EXP-V2-07: Overlap = 39.63% (Independent)
- [PASS] EXP-V2-02 vs EXP-V2-03: Overlap = 6.55% (Independent)
- [PASS] EXP-V2-02 vs EXP-V2-04: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-02 vs EXP-V2-05: Overlap = 3.86% (Independent)
- [PASS] EXP-V2-02 vs EXP-V2-06: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-02 vs EXP-V2-07: Overlap = 8.74% (Independent)
- [PASS] EXP-V2-03 vs EXP-V2-04: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-03 vs EXP-V2-05: Overlap = 3.02% (Independent)
- [PASS] EXP-V2-03 vs EXP-V2-06: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-03 vs EXP-V2-07: Overlap = 13.08% (Independent)
- [PASS] EXP-V2-04 vs EXP-V2-05: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-04 vs EXP-V2-06: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-04 vs EXP-V2-07: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-05 vs EXP-V2-06: Overlap = 0.0% (Independent)
- [PASS] EXP-V2-05 vs EXP-V2-07: Overlap = 12.67% (Independent)
- [PASS] EXP-V2-06 vs EXP-V2-07: Overlap = 0.0% (Independent)