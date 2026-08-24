# AXIOM Backend

Binance Spot Testnet execution engine with a Gemini-gated decision layer.

AXIOM runs as a persistent async process on Render or locally, exposing a FastAPI monitoring and control API for the frontend.

## Project Links

- **Live Demo:** https://axiom-frontend-orpin.vercel.app/
- **Frontend Repository:** https://github.com/Novadgaf-stack/axiom-frontend
- **Backend API:** https://axiom-backend-qgqk.onrender.com/
- **Backend Repository:** https://github.com/Novadgaf-stack/axiom-backend

## What Changed from the Original Codebase

The original `weex_brain/` code connected to **WEEX live futures**, did not include an AI layer, stored real API credentials in plaintext, and submitted a market order when the server started.

Those behaviors do not carry forward. AXIOM uses:

- Binance Spot **Testnet** execution by default;
- Gemini as a gated advisory layer;
- deterministic, code-enforced risk management; and
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
  config.py       Solana Devnet endpoint and environment settings.
  schemas.py      Structured agent-decision schema.
  policy_gate.py  Deterministic notional and rate-limit checks.
  rpc_simulator.py
                  Pre-flight Solana RPC transaction simulation.
  solana_client.py
                  Isolated Devnet signer and broadcaster.
  router.py       FastAPI routes for /api/solana/*.
