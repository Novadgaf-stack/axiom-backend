# Nexus-7 Trading Engine

Binance Spot Testnet execution engine with a Gemini-gated decision layer.
Built to run 24/7 as a persistent process (Render Web Service or local),
exposing a monitoring/control API for a separate frontend.

## What changed from the original codebase

The original `weex_brain/` code connected to **WEEX live futures**, not
Binance, had no AI layer at all, hardcoded real API credentials in plaintext,
and auto-fired a market order on server startup with no risk controls. None
of that carried forward. This is a new implementation built to the original
spec: Binance Spot **Testnet**, Gemini as a gated advisory layer, real risk
management, and no hardcoded secrets anywhere.

## Architecture

```
app/
  config.py       Settings from environment only — no hardcoded secrets.
  exchange.py     ccxt wrapper for Binance (testnet by default), retries
                  on transient errors only.
  indicators.py   EMA/RSI/ATR/MACD from OHLCV -> quantitative "technical bias".
  ai_analyst.py   Gemini call with enforced JSON schema + pydantic validation.
                  Never trusted alone (see strategy.py).
  strategy.py     THE decision gate: trade only fires if technical bias and
                  Gemini's action agree AND confidence > MIN_CONFIDENCE_SCORE.
  risk.py         Position sizing (% equity risked), ATR-based SL/TP,
                  daily loss circuit breaker.
  engine.py       The 24/7 async loop. Wrapped so one bad symbol/cycle
                  never kills the process.
  state.py        In-memory state shared between the loop and the API.
  db.py           SQLite audit trail (trades, decisions, equity curve) —
                  survives restarts.
  api.py          FastAPI routes for monitoring + control (pause/resume/kill).
  main.py         Wires it together: FastAPI app + background engine task
                  in ONE persistent process.
```

### Why one process, not split across Vercel + Render

The trading loop is an infinite `while` loop that must keep running between
cycles. Vercel functions (and serverless generally) are frozen or killed
between invocations — putting the loop there would silently stop trading.
So:

- **This engine** (loop + API) deploys to **Render as a Web Service**
  (persistent, not serverless). `render.yaml` is included.
- **Your Next.js frontend** deploys to **Vercel** as normal, and calls this
  engine's API over HTTPS for monitoring. It never runs the loop itself.

If you outgrow a single instance, split the loop into a Render **Background
Worker** (no HTTP) and run `api.py` as its own Web Service, with both reading
shared state from Postgres/Redis instead of the in-memory `state.py`. Not
needed for one engine instance.

### 24/7 Continuous Operation & Render Free Tier

- **Internal Keep-Alive**: `app/main.py` runs an automatic background keep-alive task that executes a heartbeat every 4 minutes to keep the event loop warm and active.
- **Render Free Tier Spin-Down Prevention**: Render automatically puts free Web Services to sleep after **15 minutes of HTTP inactivity**. To ensure continuous 24/7 trading on Render free tier, configure a free external uptime monitor (such as [UptimeRobot](https://uptimerobot.com) or [Cron-job.org](https://cron-job.org)) to perform an HTTP GET on `https://<your-render-app>.onrender.com/health` every 5 minutes.
- **Monitoring Health**: Access `/health` or `/api/status` to view real-time diagnostics (`engine_task_alive`, `keep_alive_active`, `trading_active`, `halt_reason`, `config_problems`).


## Safety model (read this before enabling live orders)

1. **Dual confirmation required.** A trade only executes if the quantitative
   technical bias (EMA/RSI/MACD) and Gemini's directional call **agree**, and
   Gemini's `confidence_score` exceeds `MIN_CONFIDENCE_SCORE` (default 85).
   Any disagreement, low confidence, or malformed AI response collapses to
   HOLD — this is enforced in code (`strategy.py`), not by prompting alone.
2. **Every order carries an exchange-side OCO bracket** (stop-loss + take-profit)
   placed immediately after the entry fills, so the position is protected even
   if this process crashes or restarts.
3. **Position sizing is risk-based and capped twice**: sized so a stop-loss
   hit loses exactly `RISK_PER_TRADE_PCT` of equity, then hard-capped at
   `MAX_POSITION_PCT` of equity regardless.
4. **Daily loss circuit breaker**: once realized losses in a UTC day reach
   `MAX_DAILY_LOSS_PCT`, no new entries are opened until the day rolls over.
5. **Kill switch**: `POST /api/engine/kill-switch` halts the engine
   immediately (existing OCO brackets on the exchange still protect any open
   position). Clearing a halt requires a restart, not just a resume call —
   this is deliberate, so a halt can't be casually waved off mid-incident.
6. **`BINANCE_TESTNET=false` is flagged by config validation** as something
   that must be a deliberate choice — the engine will log it loudly on
   startup rather than silently accepting it.
7. **Entries use a slippage-capped marketable limit order**, not a blind
   market order, and are skipped entirely if the live price has drifted too
   far from the candle the signal was computed on (stale-signal guard).
8. **A symbol enters cooldown after a losing trade** so the bot doesn't
   immediately re-enter the same setup that just stopped it out.
9. **The daily-loss circuit breaker survives restarts** — it rehydrates
   today's realized PnL from the trade log on startup, so a Render redeploy
   mid-day can't accidentally hand the bot a fresh loss budget.
10. **If both the OCO bracket and a fallback stop-loss fail to place**, the
    engine halts new entries immediately, but position monitoring keeps
    running and will manually close that specific position if price reaches
    its intended stop-loss or take-profit — a halt stops new risk, it never
    stops watching existing risk.

You told me you want the engine to trade autonomously once configured, with
no manual per-trade arming step — that's what's implemented. The circuit
breakers above are the safety net for that choice; they run automatically,
they don't require you to be watching.

## Setup

```bash
cp .env.example .env
# fill in BINANCE_API_KEY/SECRET from https://testnet.binance.vision
# fill in GEMINI_API_KEY from https://aistudio.google.com/apikey
# generate API_AUTH_TOKEN: python -c "import secrets; print(secrets.token_urlsafe(32))"

pip install -r requirements.txt
python test_connection.py   # verify both integrations before running live
uvicorn app.main:app --reload
```

Consider starting with `TRADING_ENABLED=false` for a day to watch the
`/api/decisions` log and confirm the signals look sane before flipping it on.

## Deploying

1. Push this repo to GitHub.
2. Render dashboard → New → Blueprint → point at the repo (`render.yaml` is
   picked up automatically).
3. Fill in the `sync: false` secrets (`BINANCE_API_KEY`, `BINANCE_API_SECRET`,
   `GEMINI_API_KEY`, `API_AUTH_TOKEN`) in the Render dashboard — never in the
   repo.
4. Set `ALLOWED_ORIGINS` to your Vercel frontend's URL.

## API contract (for your Next.js frontend)

All routes except `/health` require `Authorization: Bearer <API_AUTH_TOKEN>`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Unauthenticated liveness check |
| GET | `/api/status` | Engine status, config, uptime, last error |
| GET | `/api/positions` | Currently open positions |
| GET | `/api/trades?limit=50` | Trade history |
| GET | `/api/decisions?limit=50` | Full decision audit trail, including rejected/HOLD calls and why |
| GET | `/api/equity-curve?limit=500` | Equity snapshots over time |
| POST | `/api/engine/pause` | Pause new entries (existing positions keep their exchange-side brackets) |
| POST | `/api/engine/resume` | Resume from pause (fails if halted) |
| POST | `/api/engine/kill-switch` | Emergency halt; requires a restart to clear |

## What's intentionally out of scope here

- I did not rebuild your Vite/Supabase frontend into Next.js — you already
  have a frontend stack; this just gives it something real to call. Say the
  word if you want the frontend rebuilt against this API next.
- Margin/short selling isn't wired up — this is spot-only, so `SHORT` signals
  from Gemini are logged for visibility but not executed. Say if you want
  Binance USD-M Futures Testnet instead, which supports real shorts.

## Backtesting (`backtest.py`)

Before trusting this strategy with capital, even on testnet, run it against
history:

```bash
# Fast smoke test with synthetic data — proves the harness mechanics work,
# proves NOTHING about real market edge:
python backtest.py --source synthetic --days 180 --mode technical_only

# Real historical data, comparing "trade every technical signal" against
# an AI-confidence-gated heuristic and a random-noise control:
python backtest.py --source binance --symbol BTC/USDT --timeframe 15m \
    --days 365 --compare
```

It reuses `app/indicators.py`, `app/risk.py`, and `app/strategy.py`
unmodified — the same gating and sizing logic under test, not a
reimplementation that could drift out of sync with the live engine. See
`backtest/` for the mock AI analyst, data ingestion, simulator, and metrics
modules, and the module docstrings for the look-ahead-bias discipline and
same-bar SL/TP-conflict assumptions. `python backtest.py --help` lists every
tunable (fees, slippage, risk parameters, confidence threshold, etc.).

**Read the numbers skeptically.** A clean backtest is necessary but not
sufficient — it doesn't account for real order-book depth, and `ai_mirror`
mode is a heuristic stand-in for Gemini, not Gemini itself (only `--mode
ai_live` makes real calls, and it's slow/costly/rate-limited by design). The
`--compare` output's job is to tell you whether the AI confidence gate is
adding real filtering value over trading every technical signal, or just
adding latency and cost.
