# Superteam Agentic Engineering Grant Application — Nexus-7 Solana Agent Layer

**Project Name:** Nexus-7 Solana Devnet Signal Guard & On-Chain Audit Vault  
**Applicant:** Nexus-7 Development Team  
**Grant Category:** Agentic Engineering ($200 USDG)  
**Target Blockchain:** Solana Devnet  

---

## Executive Summary

Nexus-7 is an open-source quantitative research, backtesting, and trading engine built in Python/FastAPI. It features tick-level data ingestion, dual-confirmation strategy gating, strict portfolio risk controls, and automated testnet execution.

This grant project extends Nexus-7 by building an isolated, non-custodial **Solana Devnet Agent Layer**. When Nexus-7 evaluates market context and generates strategy signals, the Solana Agent Layer validates the decision through a deterministic policy gate, simulates transaction execution via Solana RPC (`simulateTransaction`), and commits verified audit state and Devnet SPL test transactions to Solana Devnet.

---

## 1. Capabilities Breakdown

### ALREADY COMPLETED (Verifiable in Repository)
- **Quantitative Engine Core (`app/engine.py`, `app/indicators.py`)**: Async continuous loop processing Technical Analysis (EMA, RSI, ADX, MACD, ATR) against market data.
- **AI Analyst Advisory Layer (`app/ai_analyst.py`)**: Structured Gemini API integration returning validated directional bias and confidence scoring.
- **Dual-Confirmation Decision Gate (`app/strategy.py`)**: Trade signals are rejected unless technical bias and AI action agree AND confidence score exceeds threshold.
- **Risk Management & Circuit Breakers (`app/risk.py`)**: Hard position sizing caps, 3% daily loss circuit breaker, and 15% maximum portfolio drawdown guard (V10 audit).
- **Execution & Persistence (`app/exchange.py`, `app/db.py`)**: Market limit order execution with OCO brackets on Binance Spot Testnet, backed by SQLite audit tables.
- **Rigorous Research Discipline (V2–V10 Audit Reports)**: Complete research history documenting strategy iteration. V10 audit report (`research_v10_real_data_and_drawdown_report.md`) explicitly concludes `REJECTED (NO EDGE PROVEN)`. Live real-money trading is strictly hard-locked.

### GRANT-FUNDED BUILD (To Be Implemented under $200 USDG Grant)
- **Solana Agent Layer (`solana_agent/`)**: An isolated module providing clean interfaces between Nexus-7 signals and Solana Devnet.
- **AI Reasoning & Policy Validation Gate (`solana_agent/policy_gate.py`)**: Deterministic policy checker enforcing risk rules (max SOL/token per tx, rate limits, parameter sanity).
- **Transaction Simulation Engine (`solana_agent/rpc_simulator.py`)**: Real Solana RPC pre-flight simulation via `simulateTransaction` before signing.
- **Non-Custodial Signer & Broadcaster (`solana_agent/solana_client.py`)**: Keypair isolated signing and Devnet transaction broadcasting (SPL token swap simulation / Memo audit log).
- **Structured Agent Decision Schema**:
  ```json
  {
    "decision": "EXECUTE_DEVNET_SWAP",
    "confidence": 0.88,
    "reason": "EMA trend bull & Gemini AI score 88% cleared policy",
    "risk_check": "PASS",
    "solana_simulation": "SUCCESS",
    "tx_signature": "5K...devnet"
  }
  ```
- **Automated Test Suite (`tests/test_solana_agent.py`)**: Comprehensive tests for policy violations, simulation failures, invalid agent decisions, and key isolation.

### FUTURE (Outside Grant Scope)
- Mainnet deployment or real-money Solana liquidity pool interactions.
- Multi-validator consensus for agent decision gating.
- Full-scale cross-chain arbitrage or high-frequency DEX execution.

---

## 2. Honest Disclosure & Constraints

1. **No Proven Edge**: Nexus-7 research (V2–V10) has not proven a profitable trading edge in live markets. We make zero claims of profitability.
2. **Devnet Only**: All Solana transactions operate exclusively on Solana Devnet.
3. **Safety Locks Preserved**: The existing `BINANCE_TESTNET=true` lock and live trading safety gates will remain untouched.

---

## 3. Grant Fund Allocation ($200 USDG)

- **Tranche 1 ($100 USDG Upfront)**: Architecture design, specification artifacts, agent engineering setup, AI coding tool subscriptions (receipts attached).
- **Tranche 2 ($100 USDG Post-Ship)**: Delivery of working Devnet MVP, automated test suite passing, verified Solana Devnet Explorer transaction signatures, complete open-source GitHub repository update.
