
# AXIOM Solana Devnet Agent Layer — Technical Specification

## 1. Overview and goals

The AXIOM Solana Devnet Agent Layer is an isolated module for on-chain audit and execution activity on Solana Devnet. It extends the AXIOM backend without changing the Binance Spot Testnet engine's core decision or risk path.

Its purpose is to demonstrate an agentic, policy-gated pipeline that:

1. consumes quantitative strategy signals;
2. validates a structured decision against deterministic on-chain risk limits;
3. simulates the proposed transaction through Solana RPC; and
4. signs and broadcasts an eligible transaction on Devnet without exposing private-key material or compromising the core engine.

This specification describes the intended architecture. It does not assert that a Devnet transaction has been executed or that a deployment is complete.

## 2. Component boundaries and isolation

```text
AXIOM Engine (FastAPI + async loop)
  │
  ├─► app/engine.py           Core engine boundary
  ├─► app/strategy.py         Core strategy boundary
  ├─► app/risk.py             Core risk-control boundary
  └─► app/api.py              Read-only signal/query boundary
  
         │  Signal output / REST read
         ▼
solana_agent/                 Isolated extension module
  ├─► config.py               Solana RPC endpoint and Devnet settings
  ├─► schemas.py              Structured agent-decision schema
  ├─► policy_gate.py          Deterministic risk and rate-limit checks
  ├─► rpc_simulator.py        Pre-flight `simulateTransaction` call
  ├─► solana_client.py        Devnet keypair signer and broadcaster
  └─► router.py               FastAPI `/api/solana/*` routes
```

The module boundary is intentional: removing `solana_agent/` should leave the AXIOM engine able to continue independently. Failures in the extension must not terminate the core async trading loop.

## 3. Structured agent decision schema

Each Solana-layer decision follows a strict Pydantic JSON schema. The example below is illustrative; it is not an executed transaction record.

```json
{
  "decision_id": "SOL-DEV-20260813-001",
  "symbol": "SOL/USDT",
  "action": "EXECUTE_DEVNET_SWAP",
  "confidence_score": 0.88,
  "reasoning": "Technical EMA trend bull and Gemini AI score 88% cleared policy",
  "policy_check": {
    "passed": true,
    "max_sol_cap_valid": true,
    "rate_limit_valid": true,
    "rejection_reason": null
  },
  "simulation_result": {
    "simulated": true,
    "success": true,
    "logs": [
      "Program log: Instruction: Transfer",
      "Program consumed 14200 of 200000 compute units"
    ],
    "error": null
  },
  "execution": {
    "status": "PENDING_DEVNET_AIRDROP",
    "cluster": "devnet",
    "tx_signature": null,
    "timestamp_utc": "2026-08-14T09:00:00Z"
  }
}
```

The schema captures the decision, policy outcome, simulation outcome, and execution state separately. A `tx_signature` remains `null` until a transaction is actually broadcast and its result is recorded.

## 4. Key management and security model

- **Environment-based keypair:** Load the Devnet private key only from `SOLANA_DEVNET_PRIVATE_KEY` in the runtime environment.
- **LLM isolation:** Do not include private keys in LLM prompts, Gemini requests, context windows, tool inputs, logs, or telemetry.
- **Devnet hard lock:** Configure the layer for `https://api.devnet.solana.com` and reject mainnet endpoints in `config.py`.
- **Policy before signing:** Enforce notional and rate limits in `policy_gate.py` before simulation, signing, or broadcast.
- **Simulation before broadcast:** Require a successful Solana RPC `simulateTransaction` result before a transaction can proceed.

## 5. Technology stack

| Component | Technology |
| --- | --- |
| Runtime | Python `3.10+` |
| Solana integration | `solders` and `solana` Python SDKs for transaction construction, signing, and RPC simulation |
| API and validation | FastAPI and Pydantic v2 |
| Core-engine boundary | AXIOM FastAPI backend and async execution loop |

## 6. Validation expectations

Implementation should be considered ready for grant evidence only when the following are demonstrated by actual artifacts:

- automated tests for policy rejection, Devnet locking, simulation failure, key isolation, and core-engine independence;
- a successful Devnet simulation before any signing attempt;
- a verified Devnet transaction signature, if transaction execution is included in the milestone; and
- sanitized logs or receipts that demonstrate the workflow without revealing secrets.

Refer to `TESTING_PLAN.md`, `SECURITY_MODEL.md`, and `MILESTONES.md` for the related validation criteria and schedule.
