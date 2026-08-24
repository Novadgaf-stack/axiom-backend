# AXIOM Solana Devnet Agent Layer — Implementation Plan

## Goal

Implement an isolated, security-focused Solana-native agent layer for AXIOM. The layer operates only on Solana Devnet and is planned as part of the Superteam `$200 USDG` Agentic Engineering Grant work.

The implementation must preserve the existing Binance Spot Testnet engine boundary: Solana-layer failures, configuration, and execution paths must not modify or interrupt `app/engine.py` or `app/risk.py`.

## Phase 1 — Environment and receipt setup

- Install the required Solana Python packages: `solders` and `solana`.
- Add `SOLANA_DEVNET_RPC_URL` and `SOLANA_DEVNET_PRIVATE_KEY` placeholders to `.env.example`.
- Keep Devnet private-key material in environment-managed secrets only.
- Collect and verify eligible AI-tool receipts required by the grant process.

**Deliverables**

- Updated dependency manifest.
- Sanitized `.env.example` entries with no real credentials.
- Receipt and environment-setup evidence, where applicable.

## Phase 2 — Core isolated module

Create the following `solana_agent/` package structure:

| File | Responsibility |
| --- | --- |
| `solana_agent/__init__.py` | Package initialization |
| `solana_agent/config.py` | Solana Devnet RPC validation and rejection of mainnet URLs |
| `solana_agent/schemas.py` | `SolanaAgentDecision` Pydantic model |
| `solana_agent/policy_gate.py` | Deterministic pre-gates: maximum `0.1 SOL` per Devnet transaction and five transactions per hour |
| `solana_agent/rpc_simulator.py` | Solana RPC `simulateTransaction` handler |
| `solana_agent/solana_client.py` | Environment-backed Devnet signing and broadcast client |
| `solana_agent/router.py` | FastAPI routes for status, evaluation, and history |

**Implementation rules**

- Reject non-Devnet RPC endpoints before any signing path is available.
- Apply the policy gate before simulation, signing, or broadcast.
- Require a successful pre-flight simulation before broadcast.
- Never pass private keys into prompts, API responses, logs, or telemetry.

## Phase 3 — FastAPI integration and signal adapter

- Register `solana_agent/router.py` from `app/main.py` under the `/api/solana` prefix.
- Provide the planned endpoints:
  - `GET /api/solana/status`
  - `POST /api/solana/evaluate`
  - `GET /api/solana/history`
- Consume AXIOM signals through a read-only signal or REST boundary.
- Preserve zero direct mutation of `app/engine.py` and `app/risk.py`.

**Acceptance criteria**

- The router can be disabled or removed without stopping the core AXIOM process.
- Solana-agent errors are contained and recorded without terminating the async engine loop.

## Phase 4 — Automated test suite

Create `tests/test_solana_agent.py` to cover:

- rejection of a SOL amount above the Devnet policy cap;
- hourly rate-limit rejection;
- successful and failed RPC simulation handling;
- non-custodial key isolation, including confirmation that prompt context does not receive the keypair; and
- normal core-engine behavior when `solana_agent/` is disabled or raises an exception.

The expanded matrix and acceptance conditions are documented in `TESTING_PLAN.md`.

## Phase 5 — Devnet verification and evidence assembly

- Execute only eligible test signals against Solana Devnet.
- Capture a Solana Explorer Devnet transaction signature only after an actual transaction is broadcast.
- Preserve dated, unmodified test output from the full suite.
- Assemble `EVIDENCE.md` and the grant-submission checklist using sanitized artifacts.

Do not represent a transaction, test result, deployment, or receipt as completed until its supporting evidence exists.

## Verification commands

Run these commands from the backend repository root on Windows:

```powershell
# Compile Python sources.
.\.venv\Scripts\python.exe -m py_compile solana_agent\*.py tests\*.py

# Run the full suite, including Solana-agent tests.
.\.venv\Scripts\python.exe -m pytest
```

## Completion checklist

- [ ] Dependencies and environment placeholders are configured without secrets.
- [ ] The Solana module is isolated from the AXIOM core engine.
- [ ] Devnet-only validation, policy gates, and pre-flight simulation are implemented.
- [ ] Automated tests pass in an actual recorded run.
- [ ] Any Devnet transaction signature is verified in Solana Explorer.
- [ ] The evidence package contains only sanitized, verifiable artifacts.
