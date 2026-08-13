# IMPLEMENTATION_PLAN.md — Nexus-7 Solana Agent Layer

## 1. Goal

Implement an isolated, secure, Solana-native Agent Layer for Nexus-7 operating strictly on Solana Devnet under the Superteam $200 USDG Agentic Engineering Grant.

---

## 2. Phase-by-Phase Plan

### Phase 1: Environment & Tool Receipt Setup
- Install official Solana Python packages (`solders`, `solana`).
- Configure `.env.example` with `SOLANA_DEVNET_RPC_URL` and `SOLANA_DEVNET_PRIVATE_KEY`.
- Collect and verify $200 AI tool receipts for grant compliance.

### Phase 2: Core Module Implementation (`solana_agent/`)
- `solana_agent/__init__.py`: Package initialization.
- `solana_agent/config.py`: Devnet RPC URL validation (reject mainnet URLs).
- `solana_agent/schemas.py`: `SolanaAgentDecision` Pydantic model.
- `solana_agent/policy_gate.py`: Deterministic risk checks (max 0.1 SOL/tx on Devnet, max 5 tx/hour).
- `solana_agent/rpc_simulator.py`: `simulateTransaction` RPC handler.
- `solana_agent/solana_client.py`: Devnet transaction signer & broadcaster.
- `solana_agent/router.py`: FastAPI endpoints `/api/solana/status`, `/api/solana/evaluate`, `/api/solana/history`.

### Phase 3: Fast API Integration & Signal Adapter
- Include `solana_agent/router.py` into `app/main.py` under the `/api/solana` prefix.
- Ensure zero mutation to existing `app/engine.py` or `app/risk.py`.

### Phase 4: Automated Test Suite (`tests/test_solana_agent.py`)
- Test policy gate rejection on oversized SOL amount.
- Test rate-limit policy failure.
- Test RPC simulation success vs failure handling.
- Test non-custodial key isolation (verify prompt context never receives keypair).
- Test system operation when `solana_agent` is disabled.

### Phase 5: Devnet Verification & Evidence Assembly
- Execute test signals against Solana Devnet.
- Record transaction signatures on Solana Explorer (Devnet).
- Package `EVIDENCE.md` and submission checklist.

---

## 3. Verification Commands

```bash
# Compile and lint
.\.venv\Scripts\python.exe -m py_compile solana_agent/*.py tests/*.py

# Run full test suite including Solana Agent tests
.\.venv\Scripts\python.exe -m pytest
```
