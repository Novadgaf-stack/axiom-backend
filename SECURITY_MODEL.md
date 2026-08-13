# SECURITY_MODEL.md — Threat Model & Security Controls

## 1. Core Security Principles

1. **Zero Prompt Key Exposure**: Private keys and wallet seed phrases are never included in LLM system prompts, context windows, or API calls.
2. **Deterministic Policy Pre-Gates**: AI decision outputs cannot execute directly; every instruction must pass static code assertions (`policy_gate.py`).
3. **Mandatory Pre-Flight Simulation**: No transaction is signed without first passing `simulateTransaction` on Solana RPC.
4. **Devnet Isolation**: Hard-coded cluster checks reject any RPC endpoint that is not Solana Devnet.
5. **Preservation of Existing Risk Controls**: Nexus-7 Binance Testnet risk manager (`app/risk.py`), daily loss circuit breaker, and 15% drawdown cap remain 100% active and untouched.

---

## 2. Threat Matrix & Defense Mechanisms

| Threat / Attack Vector | Risk Level | Defense Control |
| :--- | :---: | :--- |
| **Prompt Injection trying to extract keys** | High | Private key never exists in prompt memory space; key loading is isolated to `solana_client.py`. |
| **AI hallucinating 1000 SOL transaction** | Critical | Policy gate enforces hard limit of 0.1 SOL per Devnet transaction in Python code. |
| **Accidental Mainnet Execution** | Critical | `config.py` validates `SOLANA_DEVNET_RPC_URL` and rejects `mainnet-beta` strings. |
| **Malicious RPC Node Injection** | Medium | Strict TLS verification and fallback to official Solana Foundation Devnet RPC nodes. |
| **Cascading Failure from Solana Outage** | Medium | Decoupled architecture: if Solana Devnet RPC is down, core Nexus-7 trading loop continues operating normally. |

---

## 3. Key Management Architecture

```
[.env] → SOLANA_DEVNET_PRIVATE_KEY
             │
             ▼ (Loaded locally in python)
  [solana_agent/solana_client.py]
             │
             ├─► Keypair.from_base58_string(...)
             └─► Sign VersionedTransaction
```

The private key is never passed across network requests, exposed via API endpoints, or shared with AI sub-agents.
