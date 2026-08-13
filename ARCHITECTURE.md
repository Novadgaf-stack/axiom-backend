# ARCHITECTURE.md — Nexus-7 System Architecture & Solana Extension

## 1. Core Architecture Overview

Nexus-7 follows a decoupled, layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Application                   │
│                     (app/main.py, app/api.py)               │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────┐    ┌──────────────────────────┐
│      Trading Engine         │    │   Solana Agent Module    │
│      (app/engine.py)        │    │     (solana_agent/)      │
│  - 24/7 Async Polling Loop  │    │  - Policy Validation     │
│  - CCXT Binance Testnet     │    │  - RPC Simulation        │
│  - OCO Order Reconciliation │    │  - Devnet Signer         │
└──────────────┬──────────────┘    └──────────┬───────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────┐    ┌──────────────────────────┐
│    Strategy & Risk Core     │    │   Solana Devnet Venue    │
│  - app/indicators.py        │    │  - https://api.devnet.   │
│  - app/ai_analyst.py        │    │    solana.com            │
│  - app/strategy.py          │    │  - Devnet SPL Tokens     │
│  - app/risk.py (15% DD cap) │    │  - On-Chain Audit Memo   │
└─────────────────────────────┘    └──────────────────────────┘
```

---

## 2. Component Decoupling Strategy

1. **Nexus-7 Core**: Functions independently. Reads market data, evaluates indicators, queries Gemini, applies risk rules, logs to SQLite.
2. **Solana Agent Layer**: Receives read-only `Decision` context from Nexus-7. Executes Devnet-specific simulation and policy verification before broadcasting to Solana Devnet.
3. **Fail-Safe Isolation**: Any error in the Solana RPC or Devnet wallet does not stop or crash the main Nexus-7 trading loop.

---

## 3. Data & Decision Flow Matrix

| Component | Ingests | Outputs | Action |
| :--- | :--- | :--- | :--- |
| `app/strategy.py` | OHLCV + Order Book + AI | `Decision(action, confidence)` | Produces strategy signal |
| `solana_agent/policy_gate.py` | `Decision` + Policy Config | `PolicyResult(passed, reason)` | Validates risk boundaries |
| `solana_agent/rpc_simulator.py` | Unsigned Tx Bytes | `SimulationResult(success, logs)` | Pre-flight RPC simulation |
| `solana_agent/solana_client.py` | Signed Tx Bytes | `TxSignature` | Broadcasts to Devnet |
