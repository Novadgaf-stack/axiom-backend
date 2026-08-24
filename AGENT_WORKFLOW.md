# AXIOM Agentic Engineering Lifecycle

## Overview

The Superteam Agentic Engineering Grant calls for a clear demonstration of an AI-assisted software-development workflow alongside a structured runtime agent layer. AXIOM documents both: the human-reviewed engineering lifecycle used to plan and build the work, and the deterministic runtime controls that constrain AI-assisted decisions.

## Engineering workflow cycle

```text
1. Human objective
   Extend AXIOM with an isolated Solana Devnet agent layer.
   ↓
2. Repository analysis and architecture mapping
   Inspect the engine, strategy, risk, API, and persistence boundaries.
   ↓
3. Planning and specification — no-code-edit phase
   Create the application, project-specification, security, and test documents.
   ↓
4. Modular implementation
   Build the isolated policy gate, simulator, signer, and API router.
   ↓
5. Automated tests
   Run unit, integration, and policy tests with `pytest`.
   ↓
6. Failure diagnosis and verification
   Inspect logs and tracebacks; resolve imports, lint findings, and failures.
   ↓
7. Human review and feedback
   Review proposed changes and approve the next iteration.
   ↓
8. Version control and deployment
   Review the diff, then commit and push approved changes before a Render deployment.
   ↓
9. Devnet verification
   Review RPC simulation logs and verify any actual transaction signatures in Solana Devnet Explorer.
```

This workflow is sequential by design: planning and review precede implementation, while test results and Explorer links become evidence only after they are actually generated.

## Runtime agent decision engine

At runtime, the Solana layer is a constrained decision pipeline rather than an unconstrained LLM text generator.

```text
Market telemetry and strategy signal
              │
              ▼
      Gemini AI advisory result
              │  Raw structured decision + confidence score
              ▼
      Policy and safety gate
              │  Deterministic code-enforced checks
              ▼  PASS
      Solana RPC pre-flight simulation
              │
              ▼  SUCCESS
      Isolated local signer
              │
              ▼
      Solana Devnet broadcast
              │
              ▼
      Signature and audit record
```

The policy gate, simulation result, and Devnet cluster lock are mandatory controls. A model response does not authorize signing or broadcasting by itself.

## Human and agent responsibilities

| Stage | Human responsibility | System responsibility |
| --- | --- | --- |
| Objective and scope | Define the deliverable and approve scope changes | Preserve isolated-module boundaries |
| Planning | Review specifications and acceptance criteria | Produce structured plans and interfaces |
| Implementation | Review changes before release | Apply deterministic policy, simulation, and key-isolation controls |
| Verification | Review actual test and Explorer evidence | Record sanitized logs and decision outcomes |
| Deployment | Approve commits and production actions | Keep Devnet and Testnet safety boundaries active |

## Evidence discipline

- Do not treat a plan, code path, or diagram as evidence of execution.
- Preserve original test output when reporting test results.
- Link transaction signatures only after broadcast and independent Explorer review.
- Keep secrets and private keys out of prompts, logs, screenshots, and documentation.
- Record human approval for material scope changes or deployment actions.
