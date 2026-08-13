# PROJECT_SPEC.md — Nexus-7 Solana Devnet Agent Layer Technical Specification

## 1. Overview & Goals

The Nexus-7 Solana Devnet Agent Layer extends Nexus-7 with an isolated on-chain audit and execution module built for Solana Devnet.

The primary goal is to demonstrate genuine **Agentic Engineering**: a structured, policy-gated decision pipeline that ingests quantitative strategy signals, validates them against deterministic on-chain risk boundaries, simulates transactions via Solana RPC, and signs/broadcasts Devnet transactions without compromising key security or core trading engine integrity.

---

## 2. Component Boundaries & Isolation

```
Nexus-7 Engine (FastAPI + Async Loop)
  │
  ├─► app/engine.py           [UNTOUCHED]
  ├─► app/strategy.py         [UNTOUCHED]
  ├─► app/risk.py             [UNTOUCHED]
  └─► app/api.py              [UNTOUCHED (read-only queries)]
  
         │ (Signal output / REST read)
         ▼
solana_agent/ (NEW ISOLATED MODULE)
  ├─► config.py               [Solana RPC endpoint & Devnet settings]
  ├─► schemas.py              [Structured Agent Decision Schema]
  ├─► policy_gate.py          [Deterministic risk & rate-limit check]
  ├─► rpc_simulator.py        [Pre-flight simulateTransaction call]
  ├─► solana_client.py        [Devnet keypair signer & broadcaster]
  └─► router.py               [FastAPI router for /api/solana/*]
```

If `solana_agent/` is deleted, Nexus-7 continues running without interruption.

---

## 3. Structured Agent Decision Schema

All decisions produced by the Solana Agent Layer follow a strict Pydantic JSON schema:

```json
{
  "decision_id": "SOL-DEV-20260813-001",
  "symbol": "SOL/USDT",
  "action": "EXECUTE_DEVNET_SWAP",
  "confidence_score": 0.88,
  "reasoning": "Technical EMA trend bull & Gemini AI score 88% cleared policy",
  "policy_check": {
    "passed": true,
    "max_sol_cap_valid": true,
    "rate_limit_valid": true,
    "rejection_reason": null
  },
  "simulation_result": {
    "simulated": true,
    "success": true,
    "logs": ["Program log: Instruction: Transfer", "Program consumed 14200 of 200000 compute units"],
    "error": null
  },
  "execution": {
    "status": "EXECUTED",
    "cluster": "devnet",
    "tx_signature": "5K7x9...devnet",
    "timestamp_utc": "2026-08-13T15:00:00Z"
  }
}
```

---

## 4. Key Management & Security Model

- **Environment-based Keypair**: Devnet private key is loaded exclusively from `SOLANA_DEVNET_PRIVATE_KEY` in `.env`.
- **LLM Isolation**: Private keys are never passed into LLM prompts or Gemini API contexts.
- **Devnet Hard Lock**: RPC endpoint is hard-locked to `https://api.devnet.solana.com`. Mainnet endpoints are rejected by `config.py`.

---

## 5. Technology Stack & Dependencies

- **Python 3.10+**
- **Solana Python SDK (`solders` & `solana`)**: Modern official Solana SDKs for transaction construction, keypair signing, and RPC simulation.
- **FastAPI / Pydantic v2**: Structured API routing and schema validation.
