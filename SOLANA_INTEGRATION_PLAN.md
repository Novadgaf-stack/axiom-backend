

# AXIOM Solana Integration Plan

## 1. SDK and technology selection

| Area | Selected approach |
| --- | --- |
| Primary SDKs | `solders` and `solana` Python SDKs |
| Cluster | Solana Devnet — `https://api.devnet.solana.com` |
| API and schemas | FastAPI and Pydantic v2 |
| Key management | `SOLANA_DEVNET_PRIVATE_KEY` stored in environment-managed secrets |

The integration is Devnet-only. It does not cover mainnet deployment or real-money liquidity interactions.

## 2. Planned transaction types

1. **Devnet audit-state commitment:** a Memo instruction containing hashed signal telemetry.
2. **Devnet token-operation simulation:** an SPL Token transfer or swap instruction constructed and submitted to `simulateTransaction` before any signing or broadcast path.

The exact instruction and payload must remain within the policy limits and Devnet cluster lock.

## 3. Simulation workflow — `rpc_simulator.py`

Before a transaction is signed or broadcast, the agent must send it through Solana RPC pre-flight simulation.

```python
async def simulate_devnet_transaction(
    rpc_client, transaction: VersionedTransaction
) -> SimulationResult:
    response = await rpc_client.simulate_transaction(transaction)

    if response.value.err is not None:
        return SimulationResult(
            simulated=True,
            success=False,
            error=str(response.value.err),
            logs=response.value.logs or [],
        )

    return SimulationResult(
        simulated=True,
        success=True,
        error=None,
        logs=response.value.logs or [],
    )
```

If simulation returns an error or fails, the intended behavior is to abort before signing and broadcast, then record `solana_simulation: "FAILED"` in the decision audit trail.

## 4. Policy-gate rules — `policy_gate.py`

The policy gate applies deterministic validation before transaction construction.

| Rule | Requirement |
| --- | --- |
| SOL notional cap | A single Devnet transaction must not exceed `0.1 SOL`. |
| Frequency cap | A keypair must not submit more than five Devnet transactions per hour. |
| Confidence floor | The AXIOM strategy confidence score must exceed `85%`. |
| Cluster lock | The configured endpoint must use `devnet.solana.com`; mainnet URLs fail the policy check. |

Any failed rule prevents the flow from reaching simulation, signing, or broadcast.

## 5. Wallet and keypair management

- **Storage:** Store the keypair seed only in `SOLANA_DEVNET_PRIVATE_KEY` as an environment-managed secret.
- **Non-custodial isolation:** Instantiate the keypair only within `solana_client.py`.
- **Zero AI access:** Do not expose keypair values to Gemini prompts, API inputs, logs, telemetry, or responses.
- **Local signing only:** Create signatures locally after policy approval and successful pre-flight simulation.

## 6. Acceptance criteria

- The configured RPC endpoint is Solana Devnet and non-Devnet endpoints are rejected.
- A decision over the notional cap, rate cap, or confidence threshold is rejected deterministically.
- A failed simulation makes signing and broadcast unavailable.
- Private-key material is absent from prompts, logs, and API responses.
- Any broadcast signature is recorded only after a successful Devnet RPC response and can be checked in Solana Explorer.

See `PROJECT_SPEC.md`, `SECURITY_MODEL.md`, and `TESTING_PLAN.md` for the related architecture, safeguards, and validation plan.
