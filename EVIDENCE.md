# AXIOM — Superteam Grant Verification and Evidence Log

## Overview

This log organizes the supplied evidence for the Superteam Agentic Engineering Grant (`$200 USDG`): automated-test output, Solana Devnet readiness claims, transaction references, and AI-tool receipt status.

**Evidence boundary:** This document records project-supplied evidence. A reviewer should independently open the linked Devnet Explorer records and inspect any submitted receipt files. A Devnet transaction record alone does not establish that it was initiated by the AXIOM agent layer.

## 1. Automated test-suite evidence

The following is the supplied `pytest` output for the AXIOM backend and Solana-agent test suite.

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
plugins: anyio-4.14.2, asyncio-1.4.0

tests\test_ai_analyst.py ..........                                      [  9%]
tests\test_api_endpoints.py .......                                      [ 15%]
tests\test_chaos_certification.py ........                               [ 23%]
tests\test_confidence_and_ai.py ...                                      [ 25%]
tests\test_engine_audit_v3.py .                                          [ 26%]
tests\test_metrics_accounting.py ..                                      [ 28%]
tests\test_real_testnet_chaos.py .......                                 [ 35%]
tests\test_research_v10.py ....                                          [ 38%]
tests\test_research_v11.py ....                                          [ 42%]
tests\test_research_v4.py .....                                          [ 47%]
tests\test_research_v5.py .......                                        [ 53%]
tests\test_research_v6.py ......                                         [ 59%]
tests\test_research_v7.py .....                                          [ 63%]
tests\test_research_v8.py ......                                         [ 69%]
tests\test_research_v9.py ....                                           [ 73%]
tests\test_simulator.py ....                                             [ 76%]
tests\test_solana_agent.py .........                                     [ 85%]
tests\test_testnet_readiness.py .........                                [ 93%]
tests\test_v5_invariants.py .......                                      [100%]
====================== 113 passed, 2 warnings in 35.73s =======================
```

**Recorded result:** `113 passed, 2 warnings in 35.73s`.

For submission, retain the original terminal output with its run date, repository revision, and environment details. This document does not independently reproduce that test run.

## 2. Solana Devnet readiness record

| Verification scope | Supplied status | Supplied detail |
| --- | --- | --- |
| Solana Devnet RPC connectivity | Reported as verified | Live `AsyncClient("https://api.devnet.solana.com")` connection reported, with `get_latest_blockhash` and `get_slot` active. |
| Pre-flight transaction simulation | Reported as verified | `simulate_transaction()` pre-flight behavior reported in `rpc_simulator.py`. |
| Deterministic policy gate | Reported as verified | Python checks reported for a `0.1 SOL` maximum per transaction, five transactions per hour, and an `85%` confidence floor. |
| Devnet transaction signer | Reported as verified | Isolated non-custodial signer reported in `solana_client.py`, with Devnet transaction history referenced below. |

## 3. AI-tool receipt checklist

| Date | Service or tool | Eligible category | Amount | Supplied status |
| --- | --- | --- | ---: | --- |
| `2026-08` | AI Coding Assistant / API | AI engineering tooling | `$100.00` | Reported as verified; receipt must accompany submission |
| `2026-08` | Developer Cloud & API | AI infrastructure | `$100.00` | Reported as verified; receipt must accompany submission |
| **Total** |  |  | **`$200.00`** | **Reported as compliant** |

Receipt attachments were not included with this evidence text. Include the original receipts in the final submission package before representing them as attached or verified by a reviewer.

## 4. Supplied Solana Devnet transaction references

The project-supplied wallet and transaction details are recorded below for reviewer verification through Solana Devnet Explorer.

| Parameter | Supplied value |
| --- | --- |
| Target wallet address | `DcJHrrHSgvFpsYxqb6g97uaQTd2kE31rPUeDZTeDsjVq` |
| Network | Solana Devnet (`https://api.devnet.solana.com`) |
| Primary transaction signature | `2H2X78VUSuEBUYiNoXUcyM6TZwU1B1Mp853UFBPUVPEsx9x1HgfLSvv1ChK91wtDUQFaN5knf6Z7fPyVeVQPJkK4` |
| Explorer link | [Open primary transaction in Solana Devnet Explorer](https://explorer.solana.com/tx/2H2X78VUSuEBUYiNoXUcyM6TZwU1B1Mp853UFBPUVPEsx9x1HgfLSvv1ChK91wtDUQFaN5knf6Z7fPyVeVQPJkK4?cluster=devnet) |
| Block slot | `484083128` |
| Block time (UTC) | `2026-08-15T09:45:34+00:00` |
| Confirmation status | `finalized` |
| Execution status | `SUCCESS` |

### Additional supplied transaction references

| Signature | Explorer | Slot | Supplied status |
| --- | --- | ---: | --- |
| `2xrKCv1T4dU2aKNtE18B8n1hcE1k9DckSwDPtb7w8oXzrTjnoePutGjV7rwsCJqCV56amC9S2C8JqCNRQQmw6e4y` | [Open in Explorer](https://explorer.solana.com/tx/2xrKCv1T4dU2aKNtE18B8n1hcE1k9DckSwDPtb7w8oXzrTjnoePutGjV7rwsCJqCV56amC9S2C8JqCNRQQmw6e4y?cluster=devnet) | `484082602` | `SUCCESS (finalized)` |
| `5XR8MyqDuYxgA27U9mSV6zrGLK5vNg9Su6hv3FQ8S8k1uou2LqmTD2eePE7DvF2ujXHy6Abxq1dK75EjyymSwvmV` | [Open in Explorer](https://explorer.solana.com/tx/5XR8MyqDuYxgA27U9mSV6zrGLK5vNg9Su6hv3FQ8S8k1uou2LqmTD2eePE7DvF2ujXHy6Abxq1dK75EjyymSwvmV?cluster=devnet) | `484080566` | `SUCCESS (finalized)` |
| `3JmhioNi9C7GitZPknCfDLt6EH1Teoh2SpRZ5MpgZmr38WrYuxcZGGNR7AAoYocttBYqDgS2Gs8KhC6Q3S476DY7` | [Open in Explorer](https://explorer.solana.com/tx/3JmhioNi9C7GitZPknCfDLt6EH1Teoh2SpRZ5MpgZmr38WrYuxcZGGNR7AAoYocttBYqDgS2Gs8KhC6Q3S476DY7?cluster=devnet) | `484080375` | `SUCCESS (finalized)` |

## 5. Submission checklist

- [ ] Include the original, dated `pytest` output and repository revision.
- [ ] Provide the source test command and sanitized environment details.
- [ ] Open each linked transaction in Solana Devnet Explorer before submission.
- [ ] Include the original AI-tool receipt files and payment evidence.
- [ ] Do not publish private keys, seed phrases, API tokens, or unredacted `.env` files.
- [ ] Describe transaction references accurately; do not imply agent causation without execution logs that connect the agent decision to the signature.
