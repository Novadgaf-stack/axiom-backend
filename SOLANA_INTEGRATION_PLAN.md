# SOLANA_INTEGRATION_PLAN.md — Solana Integration Architecture

## 1. SDKs & Technology Selection

- **Primary SDK**: Modern official Python SDK (`solders` & `solana`).
- **Cluster**: Solana Devnet (`https://api.devnet.solana.com`).
- **Transaction Types**:
  1. **Devnet Audit State Commitment**: Memo instruction storing hashed signal telemetry on-chain.
  2. **Devnet Token Operation Simulation**: SPL Token transfer/swap instruction built and passed to `simulateTransaction`.

---

## 2. Transaction Simulation Workflow (`rpc_simulator.py`)

Before any transaction is signed or broadcast:

```python
async def simulate_devnet_transaction(rpc_client, tx: VersionedTransaction) -> SimulationResult:
    response = await rpc_client.simulate_transaction(tx)
    if response.value.err is not None:
        return SimulationResult(
            simulated=True,
            success=False,
            error=str(response.value.err),
            logs=response.value.logs or []
        )
    return SimulationResult(
        simulated=True,
        success=True,
        error=None,
        logs=response.value.logs or []
    )
```

If simulation fails or returns an error, the agent aborts execution immediately and logs `solana_simulation: "FAILED"`.

---

## 3. Policy Gate Validation Rules (`policy_gate.py`)

Deterministic validation before transaction construction:

1. **SOL Notional Cap**: Single transaction must not exceed 0.1 SOL on Devnet.
2. **Frequency Cap**: Maximum 5 Devnet transactions per hour per keypair.
3. **Signal Confidence Floor**: Nexus-7 strategy confidence score must exceed 85%.
4. **Cluster Lock**: Environment URL must contain `devnet.solana.com`. Mainnet URLs immediately fail policy check.

---

## 4. Wallet & Keypair Management

- **Storage**: Keypair secret seed stored in environment variable `SOLANA_DEVNET_PRIVATE_KEY`.
- **Non-Custodial Isolation**: Keypair object instantiated only within `solana_client.py`.
- **Zero AI Access**: No keypair details are accessible to Gemini prompts or API inputs.
