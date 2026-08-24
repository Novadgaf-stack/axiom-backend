

# AXIOM Security Model

## Purpose

This document describes the security controls for AXIOM's isolated Solana Devnet agent layer and its boundaries with the Binance Spot Testnet trading engine. It focuses on key handling, deterministic transaction controls, Devnet isolation, and fault containment.

## Core principles

1. **No key material in AI prompts.** Private keys and seed phrases must never be included in LLM system prompts, context windows, tool input, logs, or API calls.
2. **Deterministic policy pre-gates.** AI outputs cannot authorize execution directly. Every instruction must pass static code checks in `policy_gate.py`.
3. **Mandatory pre-flight simulation.** A transaction must pass Solana RPC `simulateTransaction` before it is signed or broadcast.
4. **Devnet-only operation.** Cluster checks reject RPC endpoints that are not Solana Devnet endpoints.
5. **Core-risk-control preservation.** The existing Binance Spot Testnet risk manager, daily-loss circuit breaker, and `15%` drawdown cap remain separate from and unaffected by the Solana extension.

## Threat matrix

| Threat or attack vector | Risk | Defense control |
| --- | :---: | --- |
| Prompt injection attempting to extract keys | High | The private key never enters the prompt-memory space. Key loading remains local to `solana_agent/solana_client.py`. |
| AI requests a `1000 SOL` transaction | Critical | Python policy code enforces a hard `0.1 SOL` maximum per Devnet transaction. |
| Accidental mainnet execution | Critical | `config.py` validates `SOLANA_DEVNET_RPC_URL` and rejects endpoints containing `mainnet-beta`. |
| Malicious RPC node injection | Medium | Enforce TLS verification and use an approved fallback list of official Solana Foundation Devnet RPC endpoints. |
| Solana Devnet RPC outage | Medium | The Solana layer is decoupled, so an outage does not stop the core AXIOM trading loop. |

## Key-management boundary

```text
[.env] → SOLANA_DEVNET_PRIVATE_KEY
             │
             ▼  Loaded locally in Python
[solana_agent/solana_client.py]
             │
             ├─► Keypair.from_base58_string(...)
             └─► Sign VersionedTransaction
```

The private key must not cross a network request boundary, appear in an API response, or be shared with an AI agent.

## Control sequence

```text
AI decision or external signal
          │
          ▼
Deterministic policy gate
  • Devnet-only endpoint
  • 0.1 SOL maximum notional
  • hourly transaction-rate cap
          │
          ▼
Solana RPC pre-flight simulation
          │
          ▼
Local signing with environment-loaded key
          │
          ▼
Devnet transaction broadcast
```

Any failed policy check or failed simulation stops the flow before signing and broadcast.

## Operational safeguards

- Store `SOLANA_DEVNET_PRIVATE_KEY` only in environment-managed secrets; never commit it to the repository.
- Keep the Solana Devnet agent layer isolated from `app/engine.py`, `app/risk.py`, and `app/strategy.py`.
- Sanitize logs and telemetry before storage or inspection.
- Reject configuration that points to Solana mainnet.
- Treat the policy gate and simulation result as mandatory execution controls, not advisory checks.

## Verification

Use the tests described in `TESTING_PLAN.md` to verify the controls. This document records the intended security model; it does not itself prove deployment state, test results, RPC behavior, or the absence of leaked secrets.
