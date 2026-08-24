# AXIOM Backend

Binance Spot Testnet execution engine with a Gemini-gated decision layer.

AXIOM runs as a persistent async process on Render or locally. It exposes a FastAPI monitoring and control API for the frontend, maintains a SQLite audit trail, and includes an isolated Solana Devnet agent layer for the Superteam Agentic Engineering Grant.

## Project Links

- **Live Demo:** [https://axiom-frontend-orpin.vercel.app/](https://axiom-frontend-orpin.vercel.app/)
- **Frontend Repository:** [https://github.com/Novadgaf-stack/axiom-frontend](https://github.com/Novadgaf-stack/axiom-frontend)
- **Backend API:** [https://axiom-backend-qgqk.onrender.com/](https://axiom-backend-qgqk.onrender.com/)
- **Backend Repository:** [https://github.com/Novadgaf-stack/axiom-backend](https://github.com/Novadgaf-stack/axiom-backend)

## What Changed from the Original Codebase

The original `weex_brain/` code connected to **WEEX live futures**, did not include an AI layer, stored real API credentials in plaintext, and submitted a market order when the server started.

Those behaviors do not carry forward. AXIOM uses:

- Binance Spot **Testnet** execution by default;
- Gemini as a gated advisory layer;
- deterministic, code-enforced risk management;
- persistent decision, trade, and equity auditing; and
- environment-based configuration with no hardcoded secrets.

## Architecture

```text
app/
  config.py       Environment-only settings; no hardcoded secrets.
  exchange.py     ccxt wrapper for Binance, testnet by default, with retries
                  for transient failures only.
  indicators.py   EMA, RSI, ATR, and MACD from OHLCV data, producing a
                  quantitative technical bias.
  ai_analyst.py   Gemini call with enforced JSON schema and Pydantic
                  validation; never trusted alone.
  strategy.py     Decision gate: execution requires technical-bias and
                  Gemini-action agreement plus sufficient confidence.
  risk.py         Equity-risk position sizing, ATR-based SL/TP, and a daily
                  loss circuit breaker.
  engine.py       Persistent async loop; a failing symbol or cycle does not
                  terminate the process.
  state.py        In-memory state shared by the engine loop and API.
  db.py           SQLite audit trail for trades, decisions, and equity data.
  api.py          FastAPI monitoring and control endpoints.
  main.py         One process containing the FastAPI app and background engine.

solana_agent/
  __init__.py     Package initialization.
  config.py       Solana Devnet endpoint and environment settings.
  schemas.py      Structured agent-decision schema.
  policy_gate.py  Deterministic notional and rate-limit checks.
  rpc_simulator.py
                  Pre-flight Solana RPC transaction simulation.
  solana_client.py
                  Isolated Devnet signer and broadcaster.
  router.py       FastAPI routes for /api/solana/*.
```

## Core Decision Flow

```text
Market data + technical indicators
                │
                ▼
      Gemini advisory result
                │
                ▼
   Strategy dual-confirmation gate
                │
                ▼
         Risk-management checks
                │
                ▼
 Binance Spot Testnet order path
                │
                ▼
 SQLite trade, decision, and equity audit trail
```

A Gemini response cannot authorize a trade by itself. The technical bias and Gemini direction must agree, and the confidence score must exceed the configured threshold.

## Deployment Model

The trading engine is a persistent `while` loop and must continue running between cycles. Serverless functions are not suitable for the engine loop.

- Deploy the AXIOM backend to **Render** as a persistent Web Service.
- Deploy the frontend to **Vercel**:
  [https://axiom-frontend-orpin.vercel.app/](https://axiom-frontend-orpin.vercel.app/)
- The frontend calls the backend over HTTPS for monitoring and controls. It does not run the trading loop.

**Backend API:** [https://axiom-backend-qgqk.onrender.com/](https://axiom-backend-qgqk.onrender.com/)

For larger deployments, split the engine into a Render Background Worker and run the API as a separate Web Service with shared state in Postgres or Redis.

### Continuous Operation

`app/main.py` includes a background keep-alive heartbeat.

If the selected Render plan can suspend an inactive service, configure an external uptime monitor to request:

```text
https://axiom-backend-qgqk.onrender.com/health
```

Use `/health` or `/api/status` to inspect diagnostics, including engine-task status, keep-alive status, trading status, halt reason, and configuration problems.

## Solana Devnet Agent Layer

AXIOM includes an isolated, non-custodial **Solana Devnet Agent Layer** for the Superteam Agentic Engineering Grant.

The Solana layer is separate from the Binance Spot Testnet engine. It receives a read-only decision context and cannot directly alter `app/engine.py`, `app/strategy.py`, or `app/risk.py`.

```text
AXIOM strategy decision
          │
          ▼
Solana policy gate and rate limits
          │
          ▼
Solana Devnet RPC pre-flight simulation
          │
          ▼
Local Devnet signing
          │
          ▼
Devnet broadcast and audit record
```

### Solana Safety Controls

- **Devnet-only lock:** Mainnet Solana endpoints are rejected.
- **Notional cap:** A single Devnet transaction must not exceed `0.1 SOL`.
- **Rate cap:** A keypair must not submit more than five Devnet transactions per hour.
- **Confidence floor:** The strategy confidence score must exceed `85%`.
- **Pre-flight simulation:** `simulateTransaction` must succeed before signing or broadcast.
- **Key isolation:** `SOLANA_DEVNET_PRIVATE_KEY` remains in environment-managed secrets and is never sent to Gemini, prompts, logs, telemetry, or API responses.
- **Failure containment:** Solana RPC or wallet errors must not stop the AXIOM core async trading loop.

### Structured Solana Decision Example

```json
{
  "decision_id": "SOL-DEV-20260813-001",
  "symbol": "SOL/USDT",
  "action": "EXECUTE_DEVNET_SWAP",
  "confidence_score": 0.88,
  "reasoning": "Technical EMA trend bull and Gemini AI score 88% cleared policy",
  "policy_check": {
    "passed": true,
    "max_sol_cap_valid": true,
    "rate_limit_valid": true,
    "rejection_reason": null
  },
  "simulation_result": {
    "simulated": true,
    "success": true,
    "logs": [],
    "error": null
  },
  "execution": {
    "status": "PENDING_DEVNET_AIRDROP",
    "cluster": "devnet",
    "tx_signature": null,
    "timestamp_utc": "2026-08-14T09:00:00Z"
  }
}
```

The example is a schema illustration, not a claim that a transaction has been broadcast.

## Safety Model

1. **Dual confirmation:** A trade executes only when the technical bias and Gemini directional call agree and Gemini’s `confidence_score` exceeds `MIN_CONFIDENCE_SCORE` (default `85`). Invalid, low-confidence, or conflicting output becomes `HOLD`.
2. **Exchange-side protection:** After entry fills, the engine places an OCO stop-loss and take-profit bracket.
3. **Risk-based sizing:** Position size targets `RISK_PER_TRADE_PCT` of equity at the stop-loss and is capped by `MAX_POSITION_PCT`.
4. **Daily-loss circuit breaker:** When realized losses reach `MAX_DAILY_LOSS_PCT` for the UTC day, no new entries open until the next day.
5. **Kill switch:** `POST /api/engine/kill-switch` halts new engine activity. Existing exchange-side OCO brackets remain active. A restart is required to clear the halt.
6. **Testnet validation:** `BINANCE_TESTNET=false` is highlighted by configuration validation instead of being accepted silently.
7. **Stale-signal protection:** Entries use a slippage-capped marketable limit order and are skipped when the live price has moved too far from the signal candle.
8. **Loss cooldown:** A symbol enters cooldown after a losing trade to prevent immediate re-entry.
9. **Restart-aware risk limit:** The daily-loss circuit breaker reloads current-day realized PnL from the trade log after restart.
10. **Bracket-failure handling:** If OCO and fallback stop-loss placement both fail, new entries halt while monitoring continues for the affected position.

## Setup

```bash
cp .env.example .env
# Add BINANCE_API_KEY and BINANCE_API_SECRET from https://testnet.binance.vision
# Add GEMINI_API_KEY from https://aistudio.google.com/apikey
# Generate API_AUTH_TOKEN:
python -c "import secrets; print(secrets.token_urlsafe(32))"

pip install -r requirements.txt
python test_connection.py
uvicorn app.main:app --reload
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Start with `TRADING_ENABLED=false` to review `/api/decisions` before enabling execution.

## Deploy to Render

1. Push the backend repository to GitHub:
   [https://github.com/Novadgaf-stack/axiom-backend](https://github.com/Novadgaf-stack/axiom-backend)
2. In Render, create a new **Blueprint** and select the repository.
3. Add these secrets in Render—never commit them:
   - `BINANCE_API_KEY`
   - `BINANCE_API_SECRET`
   - `GEMINI_API_KEY`
   - `API_AUTH_TOKEN`
   - `SOLANA_DEVNET_PRIVATE_KEY` when using the Solana Devnet layer
4. Set `ALLOWED_ORIGINS` to:

```text
https://axiom-frontend-orpin.vercel.app
```

## API Contract

**Base URL:** `https://axiom-backend-qgqk.onrender.com`

All routes except `/health` require:

```http
Authorization: Bearer <API_AUTH_TOKEN>
```

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Unauthenticated liveness check |
| `GET` | `/api/status` | Engine status, configuration, uptime, and latest error |
| `GET` | `/api/positions` | Open positions |
| `GET` | `/api/trades?limit=50` | Trade history |
| `GET` | `/api/decisions?limit=50` | Decision audit trail, including rejected and `HOLD` decisions |
| `GET` | `/api/equity-curve?limit=500` | Equity snapshots over time |
| `POST` | `/api/engine/pause` | Pause new entries while existing brackets remain active |
| `POST` | `/api/engine/resume` | Resume after pause; fails if the engine is halted |
| `POST` | `/api/engine/kill-switch` | Emergency halt; requires restart to clear |
| `GET` | `/api/solana/status` | Solana Devnet agent status |
| `POST` | `/api/solana/evaluate` | Evaluate a structured Solana Devnet decision |
| `GET` | `/api/solana/history` | Solana decision and execution history |

## Testing and Validation

Run the full test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Compile the Solana agent and test files:

```powershell
.\.venv\Scripts\python.exe -m py_compile solana_agent\*.py tests\*.py
```

The Solana test plan covers:

- oversized SOL transaction rejection;
- transaction rate-limit rejection;
- rejection of mainnet RPC endpoints;
- failed simulation handling;
- private-key isolation from prompts and logs; and
- continued core-engine operation if the Solana module fails.

Do not report a test result, Devnet transaction signature, or deployment as complete without preserving the actual output or linked evidence.

## Backtesting

Use `backtest.py` before placing confidence in the strategy, including on testnet.

```bash
# Synthetic-data smoke test: validates harness mechanics only.
python backtest.py --source synthetic --days 180 --mode technical_only

# Historical-data comparison.
python backtest.py --source binance --symbol BTC/USDT --timeframe 15m \
  --days 365 --compare
```

The harness reuses `app/indicators.py`, `app/risk.py`, and `app/strategy.py` rather than reimplementing their logic.

Treat backtest results skeptically. They do not account for real order-book depth, and `ai_mirror` mode is a heuristic stand-in for Gemini. Use `python backtest.py --help` for available options.

## Scope and Research Disclaimer

- AXIOM makes no claim of a proven profitable live-market trading edge.
- Binance execution is designed for Spot Testnet by default.
- The Solana extension is limited to Solana Devnet.
- Mainnet Solana deployment, real-money Solana liquidity interactions, margin trading, and short selling are outside this scope.
- Gemini `SHORT` signals are logged for visibility but are not executed by the spot-only engine.

## Security Checklist

- Keep exchange credentials, Gemini credentials, API tokens, and Solana private keys in environment variables only.
- Never commit `.env` files or secrets.
- Restrict `ALLOWED_ORIGINS` to `https://axiom-frontend-orpin.vercel.app`.
- Keep Solana signing keys out of prompts, logs, telemetry, and API responses.
- Review risk controls and testnet behavior before any deliberate move away from Binance Spot Testnet.
