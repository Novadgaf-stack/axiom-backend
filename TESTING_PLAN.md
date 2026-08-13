# TESTING_PLAN.md — Automated Test & Validation Suite

## 1. Overview

The testing strategy covers both unit testing of isolated components and integration testing of the agentic decision lifecycle. All tests run locally via `pytest`.

---

## 2. Test Matrix (`tests/test_solana_agent.py`)

| Test Case | Objective | Expected Outcome |
| :--- | :--- | :--- |
| `test_policy_gate_pass` | Valid decision context (0.05 SOL, 88% confidence) | `policy_check.passed == True` |
| `test_policy_gate_reject_oversized` | Decision requesting 1.5 SOL on Devnet | `policy_check.passed == False` (`reject_reason`: "sol_amount_exceeds_devnet_cap") |
| `test_policy_gate_rate_limit` | Exceeding 5 transactions per hour | `policy_check.passed == False` (`reject_reason`: "hourly_rate_limit_exceeded") |
| `test_cluster_lock_rejection` | Configured with mainnet RPC URL | Engine initialization raises `ValueError("Mainnet RPC forbidden")` |
| `test_simulation_failure_handling` | Simulated tx with bad instruction data | `simulation_result.success == False`, transaction broadcast aborted |
| `test_key_isolation` | Inspect telemetry & prompt logs | 0 occurrences of private key in prompt payloads or logs |
| `test_core_engine_independence` | Execute engine test suite when `solana_agent` throws exceptions | All 51 core Nexus-7 tests pass without error |

---

## 3. Test Execution Command

```bash
# Execute full suite including new Solana Agent test suite
.\.venv\Scripts\python.exe -m pytest
```
