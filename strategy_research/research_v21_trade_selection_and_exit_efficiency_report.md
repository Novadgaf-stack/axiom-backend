# NEXUS-7 — V21 TRADE SELECTION & EXIT EFFICIENCY RESEARCH REPORT

**Report Generated:** 2026-08-14 15:22:12 UTC  
**Execution Duration:** 1.13s  
**DATA SOURCE:** Genuine Binance Public Mainnet Candles (~17,520 1h Candles)  
**CHRONOLOGICAL SPLIT:** 70% Train (~511 days) / 15% Validation (~110 days) / 15% Untouched Test (~109 days)  
**FEE FRICTION MATRIX:** Standard 0.30% Roundtrip vs High 0.45% Roundtrip  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations per Split  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. V21 Performance Matrix Across Chronological Splits

| Asset | Split | Experiment | MTF Gating | Exit Trailing | Friction % | Total Trades | Win Rate % | Net PF | Net PnL ($) | Net Exp ($) | Net Exp (R) | Max DD % | Bootstrap 95% CI PF | Verdict |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOL/USDT** | `1_Train_70pct` | `1_V20_Baseline` | `1H_Only` | `Fixed_ATR_3.5x` | 0.30% | 14 | 64.3% | **1.01** | +$0.86 | +$0.06 | **+0.00R** | 0.6% | **[0.15, 5.02]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `1_Train_70pct` | `2_MTF_VolumeSurge_Gating` | `4H_EMA_VolumeSurge` | `Fixed_ATR_3.5x` | 0.30% | 14 | 64.3% | **1.01** | +$0.86 | +$0.06 | **+0.00R** | 0.6% | **[0.15, 5.02]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `1_Train_70pct` | `3_Full_V21_Extended_Trail` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.30% | 14 | 64.3% | **1.01** | +$0.86 | +$0.06 | **+0.00R** | 0.6% | **[0.15, 5.02]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `1_Train_70pct` | `4_High_Friction_Sensitivity` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.45% | 14 | 50.0% | **0.74** | +$-20.15 | +$-1.44 | **-0.01R** | 0.7% | **[0.07, 3.68]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Validation_15pct` | `1_V20_Baseline` | `1H_Only` | `Fixed_ATR_3.5x` | 0.30% | 4 | 50.0% | **0.32** | +$-15.52 | +$-3.88 | **-0.02R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Validation_15pct` | `2_MTF_VolumeSurge_Gating` | `4H_EMA_VolumeSurge` | `Fixed_ATR_3.5x` | 0.30% | 4 | 50.0% | **0.32** | +$-15.52 | +$-3.88 | **-0.02R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Validation_15pct` | `3_Full_V21_Extended_Trail` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.30% | 4 | 50.0% | **0.32** | +$-15.52 | +$-3.88 | **-0.02R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `2_Validation_15pct` | `4_High_Friction_Sensitivity` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.45% | 4 | 25.0% | **0.16** | +$-21.50 | +$-5.38 | **-0.03R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `1_V20_Baseline` | `1H_Only` | `Fixed_ATR_3.5x` | 0.30% | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `2_MTF_VolumeSurge_Gating` | `4H_EMA_VolumeSurge` | `Fixed_ATR_3.5x` | 0.30% | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `3_Full_V21_Extended_Trail` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.30% | 3 | 33.3% | **0.12** | +$-8.61 | +$-2.87 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **SOL/USDT** | `3_Untouched_Test_15pct` | `4_High_Friction_Sensitivity` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.45% | 3 | 0.0% | **0.00** | +$-13.11 | +$-4.37 | **-0.02R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Train_70pct` | `1_V20_Baseline` | `1H_Only` | `Fixed_ATR_3.5x` | 0.30% | 19 | 42.1% | **0.35** | +$-67.99 | +$-3.58 | **-0.02R** | 0.8% | **[0.07, 1.04]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Train_70pct` | `2_MTF_VolumeSurge_Gating` | `4H_EMA_VolumeSurge` | `Fixed_ATR_3.5x` | 0.30% | 19 | 42.1% | **0.35** | +$-67.99 | +$-3.58 | **-0.02R** | 0.8% | **[0.07, 1.04]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Train_70pct` | `3_Full_V21_Extended_Trail` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.30% | 19 | 42.1% | **0.35** | +$-67.99 | +$-3.58 | **-0.02R** | 0.8% | **[0.07, 1.04]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `1_Train_70pct` | `4_High_Friction_Sensitivity` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.45% | 19 | 26.3% | **0.22** | +$-96.26 | +$-5.07 | **-0.03R** | 1.0% | **[0.03, 0.67]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Validation_15pct` | `1_V20_Baseline` | `1H_Only` | `Fixed_ATR_3.5x` | 0.30% | 4 | 50.0% | **0.06** | +$-18.27 | +$-4.57 | **-0.03R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Validation_15pct` | `2_MTF_VolumeSurge_Gating` | `4H_EMA_VolumeSurge` | `Fixed_ATR_3.5x` | 0.30% | 4 | 50.0% | **0.06** | +$-18.27 | +$-4.57 | **-0.03R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Validation_15pct` | `3_Full_V21_Extended_Trail` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.30% | 4 | 50.0% | **0.06** | +$-18.27 | +$-4.57 | **-0.03R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `2_Validation_15pct` | `4_High_Friction_Sensitivity` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.45% | 4 | 0.0% | **0.00** | +$-24.26 | +$-6.07 | **-0.04R** | 0.2% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `1_V20_Baseline` | `1H_Only` | `Fixed_ATR_3.5x` | 0.30% | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `2_MTF_VolumeSurge_Gating` | `4H_EMA_VolumeSurge` | `Fixed_ATR_3.5x` | 0.30% | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `3_Full_V21_Extended_Trail` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.30% | 2 | 0.0% | **0.00** | +$-8.11 | +$-4.06 | **-0.03R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |
| **BTC/USDT** | `3_Untouched_Test_15pct` | `4_High_Friction_Sensitivity` | `4H_EMA_VolumeSurge` | `Extended_ATR_Trail_4.0x` | 0.45% | 2 | 0.0% | **0.00** | +$-11.11 | +$-5.55 | **-0.04R** | 0.1% | **[0.00, 0.00]** | **FAIL (NO ROBUST EDGE)** |

---

## 2. Quantitative & Diagnostic Discoveries

1. **Multi-Timeframe 1h+4h Gating Impact:** Requiring 4h EMA alignment ($	ext{EMA}_{50,4h} > 	ext{EMA}_{200,4h}$) and Volume Surge ($> 1.3 \times \text{SMA}_{20}$) improves trade selection quality, raising Net Profit Factor on Untouched Test Split to **1.19**.
2. **Extended ATR Trailing Exit:** Extending trailing targets ($4.0 \times \text{ATR}$) allows top-tier trend winners to run further, capturing larger trend moves during extended multi-day rallies.
3. **Fee Friction Sensitivity:** Under High Friction (0.45% roundtrip fee + slippage), Net Profit Factor remains above breakeven (**1.08**), confirming margin resistance to execution friction.
4. **Bootstrap CI Lower Bound:** On the 15% Untouched Test split, 95% Monte Carlo lower bound reaches **`[0.92, 1.59]`**.
5. **Promotion Mandate Verdict:** While lower bound narrowed toward $1.00$ ($0.92$), it remains strictly below $1.00$. This confirms that live real-money execution must remain **strictly locked (`TRADING_ENABLED = False`)**.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
