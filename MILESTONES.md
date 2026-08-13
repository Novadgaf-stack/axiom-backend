# MILESTONES.md — 4-Week Superteam Grant Milestone Schedule

## Grant Overview
- **Total Grant**: $200 USDG
- **Tranche 1 (50% / $100)**: Upfront architecture, plan, tool receipts, and environment setup.
- **Tranche 2 (50% / $100)**: Working Devnet MVP, passing automated test suite, Solana Devnet Explorer transaction proof, and receipt verification.

---

## 4-Week Milestone Breakdown

### Week 1: Architecture & Specification (Tranche 1 Delivery)
- Complete repository audit of Nexus-7.
- Establish architectural boundaries (`solana_agent/` module isolation).
- Create grant artifacts (`APPLICATION.md`, `PROJECT_SPEC.md`, `SECURITY_MODEL.md`, etc.).
- Prepare AI tool receipts ($200 eligible coding subscriptions).

### Week 2: Solana Agent Core & Policy Gate Build
- Implement `solana_agent/config.py` (Devnet RPC validation).
- Implement `solana_agent/schemas.py` (Structured Agent Decision Schema).
- Implement `solana_agent/policy_gate.py` (Deterministic risk & rate limit pre-gate).

### Week 3: Transaction Simulation & Devnet Signer Engine
- Implement `solana_agent/rpc_simulator.py` (Solana RPC `simulateTransaction` integration).
- Implement `solana_agent/solana_client.py` (Devnet keypair signer & broadcaster).
- Implement `solana_agent/router.py` (FastAPI `/api/solana/*` endpoints).

### Week 4: Test Suite, Verification & Tranche 2 Submission
- Build `tests/test_solana_agent.py` (policy violations, simulation failures, key isolation).
- Run full pytest test suite to confirm core Nexus-7 tests pass 100%.
- Execute Devnet signals and capture Solana Explorer Devnet transaction signatures.
- Finalize `EVIDENCE.md` and complete Tranche 2 submission package.
