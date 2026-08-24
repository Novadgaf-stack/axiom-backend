# Superteam Agentic Engineering Grant Application — AXIOM Solana Devnet Agent Layer

**Project name:** AXIOM Solana Devnet Signal Guard and On-Chain Audit Vault  
**Applicant:** AXIOM Development Team  
**Grant category:** Agentic Engineering (`$200 USDG`)  
**Target blockchain:** Solana Devnet

## Executive summary

AXIOM is a Python and FastAPI quantitative research, backtesting, and trading-engine project. It combines market-data analysis, a Gemini-gated advisory layer, deterministic strategy checks, and automated Binance Spot Testnet execution controls.

This grant project proposes an isolated, non-custodial **Solana Devnet Agent Layer**. When AXIOM generates a structured strategy decision, the extension is designed to validate it through a deterministic policy gate, run pre-flight transaction simulation with Solana RPC `simulateTransaction`, and record or execute eligible Devnet audit actions without exposing private keys or changing the core engine's risk path.

## 1. Existing AXIOM foundation

The following capabilities are reported as part of the existing AXIOM backend and should be demonstrated through repository review and the evidence package.

- **Quantitative engine core** (`app/engine.py`, `app/indicators.py`): persistent async processing of technical-analysis inputs, including EMA, RSI, ADX, MACD, and ATR.
- **AI analyst advisory layer** (`app/ai_analyst.py`): structured Gemini integration that returns validated directional bias and confidence scoring.
- **Dual-confirmation strategy gate** (`app/strategy.py`): trade signals require technical-bias and AI-directional agreement as well as a configured confidence threshold.
- **Risk controls and circuit breakers** (`app/risk.py`): position-sizing limits, a reported `3%` daily-loss circuit breaker, and a reported `15%` maximum portfolio-drawdown guard.
- **Execution and persistence** (`app/exchange.py`, `app/db.py`): slippage-capped marketable-limit execution with OCO brackets on Binance Spot Testnet and SQLite audit tables.
- **Research discipline:** the supplied V2–V10 research history includes a V10 conclusion of `REJECTED (NO EDGE PROVEN)`. AXIOM therefore makes no profitability claim, and real-money trading remains outside this grant scope.

## 2. Proposed grant-funded build

The grant-funded work focuses on the following planned deliverables.

- **Isolated Solana module** (`solana_agent/`): a clean boundary between AXIOM decision signals and Solana Devnet workflows.
- **AI reasoning and policy validation** (`solana_agent/policy_gate.py`): deterministic checks for maximum SOL or token amounts, rate limits, and parameter sanity before execution.
- **Transaction simulation** (`solana_agent/rpc_simulator.py`): Solana RPC `simulateTransaction` before signing.
- **Non-custodial Devnet signer and broadcaster** (`solana_agent/solana_client.py`): environment-managed keypair signing for Devnet broadcast and audit actions such as SPL-token test transactions or Memo entries.
- **Structured decision schema:** records the proposed action, confidence, rationale, policy result, simulation result, and transaction-signature field.
- **Automated tests** (`tests/test_solana_agent.py`): policy violations, simulation failures, invalid decisions, key isolation, and core-engine independence.

Illustrative decision record:

```json
{
  "decision": "EXECUTE_DEVNET_SWAP",
  "confidence": 0.88,
  "reason": "EMA trend bull and Gemini AI score 88% cleared policy",
  "risk_check": "PASS",
  "solana_simulation": "SUCCESS",
  "tx_signature": null
}
```

The example is a schema illustration, not a claim that a transaction has been sent.

## 3. Honest disclosure and constraints

1. **No proven market edge.** Supplied research material does not establish a profitable live-market trading edge. AXIOM makes no claim of profitability.
2. **Devnet only.** All Solana activity described in this grant scope is limited to Solana Devnet.
3. **Core protections remain separate.** The Binance Spot Testnet setting and existing live-trading safety gates remain outside the Solana extension's control.
4. **Evidence required.** Tests, Devnet transactions, deployment state, and receipt status are represented as complete only when supported by the submitted evidence.

## 4. Proposed grant allocation

| Tranche | Amount | Planned use and evidence |
| --- | ---: | --- |
| Tranche 1 — upfront | `$100 USDG` | Architecture, technical specification, agent-engineering setup, and eligible AI-tool subscription receipts |
| Tranche 2 — post-ship | `$100 USDG` | Devnet MVP, recorded automated-test run, verified Devnet Explorer transaction references, and repository update evidence |
| **Total** | **`$200 USDG`** | **Two-tranche delivery plan** |

Grant amounts and acceptance remain subject to the program's review and terms.

## 5. Submission evidence

The submission package should include:

- `PROJECT_SPEC.md`, `ARCHITECTURE.md`, `SECURITY_MODEL.md`, and `IMPLEMENTATION_PLAN.md`;
- dated automated-test output and repository revision information;
- Solana Devnet Explorer links only for actually broadcast transactions;
- sanitized configuration and key-isolation evidence; and
- original AI-tool receipt files and payment evidence.

This application distinguishes proposed work from reported or verifiable evidence and does not claim a mainnet deployment, real-money Solana execution, or proven trading profitability.
