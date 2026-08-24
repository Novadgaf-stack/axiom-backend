# AXIOM System Architecture and Solana Extension

## 1. Core architecture overview

AXIOM uses a decoupled, layered architecture. The FastAPI application hosts the persistent async trading engine and exposes API routes for monitoring and control. The Solana Devnet agent layer is an isolated extension that is intended to consume a read-only decision context and cannot control the core Binance Spot Testnet execution path directly.

```text
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                     │
│                   app/main.py · app/api.py                  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────┐    ┌──────────────────────────┐
│       Trading Engine        │    │   Solana Agent Module    │
│       app/engine.py         │    │      solana_agent/        │
│  • Persistent async loop    │    │  • Policy validation     │
│  • CCXT Binance Testnet     │    │  • RPC simulation        │
│  • OCO order handling       │    │  • Devnet signing        │
└──────────────┬──────────────┘    └──────────┬───────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────┐    ┌──────────────────────────┐
│      Strategy and Risk      │    │   Solana Devnet Venue    │
│  • app/indicators.py        │    │  • api.devnet.solana.com │
│  • app/ai_analyst.py        │    │  • Devnet SPL tokens     │
│  • app/strategy.py          │    │  • On-chain audit Memo   │
│  • app/risk.py              │    │                          │
└─────────────────────────────┘    └──────────────────────────┘
```

## 2. Component boundaries and isolation

### AXIOM core

The core engine operates independently: it reads market data, evaluates technical indicators, obtains a Gemini advisory result, applies deterministic strategy and risk rules, and writes its audit trail to SQLite.

### Solana Devnet agent layer

The extension receives a read-only `Decision` context from AXIOM. Before a Devnet transaction can proceed, it applies deterministic policy checks and Solana RPC simulation. Its scope is limited to Solana Devnet activity and audit workflows.

### Failure containment

An error in Solana RPC connectivity, Devnet wallet handling, or the extension itself must be contained so that it does not stop or crash the main AXIOM async trading loop. This is achieved by maintaining the module boundary between `solana_agent/` and the core engine, strategy, and risk files.

## 3. Data and decision flow

| Component | Ingests | Outputs | Responsibility |
| --- | --- | --- | --- |
| `app/strategy.py` | OHLCV data, order-book data, and AI advisory output | `Decision(action, confidence)` | Produces the strategy signal |
| `solana_agent/policy_gate.py` | `Decision` and policy configuration | `PolicyResult(passed, reason)` | Validates deterministic risk boundaries |
| `solana_agent/rpc_simulator.py` | Unsigned transaction bytes | `SimulationResult(success, logs)` | Performs pre-flight RPC simulation |
| `solana_agent/solana_client.py` | Transaction ready for signing | Transaction signature or error | Signs locally and broadcasts only to Devnet |

## 4. Execution-control sequence

```text
Market data + technical analysis + Gemini advisory
                         │
                         ▼
               AXIOM strategy decision
                         │
          Read-only decision context
                         ▼
        Solana policy gate and rate limits
                         │
                         ▼
          Solana Devnet RPC simulation
                         │
                         ▼
       Local Devnet signing and broadcast
```

Any rejected policy decision or failed simulation ends the Solana path before signing. The Binance Spot Testnet execution path remains separate.

## 5. Status and evidence boundary

The diagram and flows document the intended AXIOM architecture. The existence, implementation state, and runtime behavior of individual components should be demonstrated with repository code, test output, and Devnet Explorer records. See `PROJECT_SPEC.md`, `IMPLEMENTATION_PLAN.md`, `TESTING_PLAN.md`, and `EVIDENCE.md` for the corresponding scope and evidence records.
