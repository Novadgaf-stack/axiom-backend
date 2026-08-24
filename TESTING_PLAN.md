# AXIOM Testing Plan

## Purpose

This plan defines the automated checks for AXIOM's isolated Solana Devnet agent layer and its relationship to the existing Binance Spot Testnet engine. It covers component-level behavior, safety controls, and resilience when the Solana extension is unavailable.

Run the suite locally with `pytest`.

## Test scope

- **Unit tests** validate isolated policy, configuration, simulation, and key-isolation behavior.
- **Integration tests** validate the agentic decision lifecycle from decision context through policy enforcement and pre-flight simulation.
- **Regression tests** confirm that failures in `solana_agent/` do not break the core AXIOM engine test suite.

## Solana agent test matrix

The following cases belong in `tests/test_solana_agent.py`.

| Test case | Objective | Expected outcome |
| --- | --- | --- |
| `test_policy_gate_pass` | Evaluate a valid decision context of `0.05 SOL` with `88%` confidence. | `policy_check.passed == True` |
| `test_policy_gate_reject_oversized` | Evaluate a request for `1.5 SOL` on Devnet. | `policy_check.passed == False` with `reject_reason == "sol_amount_exceeds_devnet_cap"` |
| `test_policy_gate_rate_limit` | Exceed the configured limit of five transactions per hour. | `policy_check.passed == False` with `reject_reason == "hourly_rate_limit_exceeded"` |
| `test_cluster_lock_rejection` | Initialize the agent with a mainnet RPC URL. | Raises `ValueError("Mainnet RPC forbidden")` |
| `test_simulation_failure_handling` | Simulate a transaction with invalid instruction data. | `simulation_result.success == False`; broadcast is not attempted |
| `test_key_isolation` | Inspect telemetry and prompt logs. | No private key appears in prompt payloads or logs |
| `test_core_engine_independence` | Cause `solana_agent/` to raise exceptions while the core suite runs. | Core AXIOM tests complete without error from the Solana exception |

## Acceptance criteria

Before treating the Solana Devnet agent layer as validated:

1. Every test in the matrix passes locally.
2. A failed simulation prevents signing and broadcast.
3. A mainnet RPC endpoint is rejected during initialization.
4. Test logs, telemetry, and prompt payloads contain no private-key material.
5. Solana-agent failures remain isolated from the Binance Spot Testnet engine.

The plan does not assert a current test count or test result. Capture the command output separately whenever validation is run.

## Run the suite

From the backend repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

To focus on the Solana agent tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_solana_agent.py
```

## Reporting failures

For a failed run, record:

- the command used;
- the failing test name and traceback;
- the relevant sanitized configuration (never private keys or API tokens); and
- whether the failure occurred before or after policy enforcement or simulation.

