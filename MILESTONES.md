# AXIOM — Superteam Grant Milestone Schedule

## Grant overview

This schedule organizes the proposed four-week delivery plan for the Superteam Agentic Engineering Grant.

| Tranche | Proposed amount | Planned delivery evidence |
| --- | ---: | --- |
| Tranche 1 | `$100 USDG` (50%) | Architecture, plan, tool receipts, and environment setup |
| Tranche 2 | `$100 USDG` (50%) | Devnet MVP, automated-test evidence, Devnet Explorer transaction proof, and receipt verification |
| **Total** | **`$200 USDG`** | **Two-tranche grant plan** |

Amounts, acceptance criteria, and timing remain subject to the grant program's terms and approval process.

## Week 1 — Architecture and specification

**Planned Tranche 1 delivery**

- Audit the AXIOM backend repository and document the scope of the existing engine.
- Establish the isolation boundary for the `solana_agent/` module.
- Finalize the grant artifacts, including `APPLICATION.md`, `PROJECT_SPEC.md`, and `SECURITY_MODEL.md`.
- Prepare eligible AI-tool receipts and environment-setup evidence.

**Completion evidence**

- Architecture diagram and technical specification.
- Documentation of the separation between `solana_agent/` and the AXIOM engine.
- Sanitized environment-setup record and applicable tool receipts.

## Week 2 — Solana agent core and policy gate

- Implement `solana_agent/config.py` for Devnet RPC validation.
- Implement `solana_agent/schemas.py` for the structured agent-decision schema.
- Implement `solana_agent/policy_gate.py` for deterministic notional and rate-limit checks.

**Completion evidence**

- Source files for configuration, schemas, and policy enforcement.
- Tests or review artifacts showing Devnet-only configuration and policy rejection behavior.

## Week 3 — Simulation and Devnet signer

- Implement `solana_agent/rpc_simulator.py` for Solana RPC `simulateTransaction` integration.
- Implement `solana_agent/solana_client.py` for Devnet keypair signing and broadcast.
- Implement `solana_agent/router.py` for FastAPI `/api/solana/*` routes.

**Completion evidence**

- A successful, sanitized pre-flight simulation record.
- Source-level proof that signing keys remain environment-managed and isolated from AI prompts.
- API-route documentation for the Solana extension.

## Week 4 — Tests, verification, and Tranche 2 package

- Build `tests/test_solana_agent.py` for policy violations, simulation failures, key isolation, and core-engine independence.
- Run the full `pytest` suite and preserve the actual result output.
- Execute eligible Devnet signals and capture Solana Explorer Devnet transaction signatures, if execution has been completed.
- Finalize `EVIDENCE.md` and prepare the Tranche 2 submission package.

**Completion evidence**

- Dated, unmodified test output from the full suite.
- A Devnet Explorer link or transaction signature only when an actual transaction exists.
- Sanitized evidence package, including tool receipts and implementation artifacts.

## Delivery principles

- Do not represent planned work as completed work.
- Do not submit transaction signatures, deployment claims, or test-pass claims unless they are backed by verifiable evidence.
- Keep all secrets, private keys, and API tokens out of screenshots, logs, receipts, and documentation.
- Preserve the isolated-module boundary so Solana-layer failures do not affect the AXIOM core engine.
