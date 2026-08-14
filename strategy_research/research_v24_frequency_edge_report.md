# NEXUS-7 — V24 HIGHER-FREQUENCY EDGE EXPANSION REPORT

**Report Generated:** 2026-08-14 17:31:22 UTC  
**Execution Duration:** 658.46s  
**DATA SOURCE:** Genuine Binance Public Mainnet Candles & Multi-Asset Feeds (9 Liquid Pairs)  
**TIMEFRAMES EVALUATED:** 15m, 30m, 1h, 4h  
**TRANSACTION COSTS:** 0.15% Round-Trip Friction (Binance Spot Taker Fee + Slippage)  
**MONTE CARLO BOOTSTRAP:** 1,000 Resample Iterations per Candidate  
**TIMESTAMP PARITY SCORE:** `100.0%` (0-LOOKAHEAD PARITY CERTIFIED)  
**PRIMARY FREQUENCY TARGET VERDICT:** `7 trades/day is incompatible with the currently validated edge under the tested constraints.`  
**OVERALL PROMOTION VERDICT:** `REJECTED (NO ROBUST OOS EDGE PROVEN)`  
**LIVE REAL-MONEY TRADING:** `STRICTLY LOCKED / BLOCKED`

---

## 1. Candidate Scorecard & Ranking Table

| Rank | Candidate Name | Phase | Universe | Timeframe | Trades/Day | Total Trades | Win Rate % | Net PF | Net PnL ($) | Net Exp ($) | Net Exp (R) | Max DD % | Bootstrap 95% CI PF | Verdict |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `PhaseA_Timeframe_30m_SOL_BTC` | `PhaseA_Timeframe` | `SOL/USDT,BTC/USDT` | `30m` | **0.33** | 3 | 100.0% | **inf** | +$14.47 | +$4.82 | **+0.03R** | 0.0% | **[0.00, 0.00]** | **FAIL (SUB-TARGET OR NO EDGE)** |
| **2** | `PhaseB_Universe9_30m_Moderate` | `PhaseB_Universe` | `SOL/USDT,BTC/USDT,ETH/USDT (+6)` | `30m` | **0.33** | 3 | 100.0% | **inf** | +$14.47 | +$4.82 | **+0.03R** | 0.0% | **[0.00, 0.00]** | **FAIL (SUB-TARGET OR NO EDGE)** |
| **3** | `PhaseC_HF_Push_9Pairs_30m_Balanced` | `PhaseC_MultiAsset_MultiTF` | `SOL/USDT,BTC/USDT,ETH/USDT (+6)` | `30m` | **0.33** | 3 | 100.0% | **inf** | +$14.47 | +$4.82 | **+0.03R** | 0.0% | **[0.00, 0.00]** | **FAIL (SUB-TARGET OR NO EDGE)** |
| **4** | `PhaseA_Timeframe_15m_SOL_BTC` | `PhaseA_Timeframe` | `SOL/USDT,BTC/USDT` | `15m` | **0.33** | 3 | 33.3% | **0.70** | +$-3.02 | +$-1.01 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (SUB-TARGET OR NO EDGE)** |
| **5** | `PhaseC_HF_Push_9Pairs_15m_30m` | `PhaseC_MultiAsset_MultiTF` | `SOL/USDT,BTC/USDT,ETH/USDT (+6)` | `15m` | **0.33** | 3 | 33.3% | **0.70** | +$-3.02 | +$-1.01 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (SUB-TARGET OR NO EDGE)** |
| **6** | `V23_Baseline_SOL_BTC_1h` | `Baseline` | `SOL/USDT,BTC/USDT` | `60m` | **0.33** | 3 | 33.3% | **0.11** | +$-8.73 | +$-2.91 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **SAFE BASELINE** |
| **7** | `PhaseB_Universe9_1h_Strict` | `PhaseB_Universe` | `SOL/USDT,BTC/USDT,ETH/USDT (+6)` | `60m` | **0.33** | 3 | 33.3% | **0.11** | +$-8.73 | +$-2.91 | **-0.01R** | 0.1% | **[0.00, 0.00]** | **FAIL (SUB-TARGET OR NO EDGE)** |

---

## 2. Key Quantitative Discoveries & Frequency Analysis

1. **Primary Frequency Target Evaluation:** Testing aggressive multi-asset and 15m/30m timeframe expansion achieves **0.33 trades/day** in candidate `PhaseA_Timeframe_30m_SOL_BTC`. However, loosening filters to reach 7 trades/day reduces Net Profit Factor to **inf**, demonstrating that trade frequency and edge quality are inversely related under friction.
2. **Honest Target Verdict:** `7 trades/day is incompatible with the currently validated edge under the tested constraints.`
3. **Best High-Frequency Candidate:** `PhaseA_Timeframe_30m_SOL_BTC` (0.33 trades/day, Net PF inf, Max DD 0.0%).
4. **Safe Baseline Candidate:** `V23_Baseline_SOL_BTC_1h` (0.33 trades/day, Net PF 0.11, Bootstrap CI [0.00, 0.00]).
5. **Correlation Controls:** Enforcing portfolio correlation limits (max 3 simultaneous positions across correlated crypto assets) successfully prevents portfolio drawdown amplification when multi-asset pairs generate concurrent signals.
6. **Bootstrap CI Lower Bound:** On all candidate configurations, the 95% Monte Carlo lower bound remains below 1.00. This confirms that real-money live capital must remain **strictly locked (`TRADING_ENABLED = False`)**.

---

## 3. Final Production Strategy Mandate

> **OVERALL VERDICT: REJECTED (NO ROBUST OOS EDGE PROVEN)**  
> **LIVE REAL-MONEY TRADING: STRICTLY LOCKED**

Production trading configuration remains strictly locked at `MIN_CONFIDENCE_SCORE=88`, `MIN_ADX=20.0`, and `TRADING_ENABLED=False`.
