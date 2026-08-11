"""
The persistent execution engine. This is an async loop meant to run for the
life of the process (a Render Web Service / background worker, or locally) —
NOT inside a serverless function. main.py starts this as a background
asyncio task alongside the FastAPI app in the same process, so monitoring
endpoints can read `state` directly with no extra infrastructure.

Every iteration is wrapped so that a single symbol's failure (bad data,
exchange hiccup, AI error) never kills the loop — it's logged and the loop
moves on to the next symbol/cycle.
"""
import asyncio
from datetime import datetime, timezone

from app.config import settings
from app.exchange import DataExchange, ExecutionExchange, OrderRejected
from app.ai_analyst import AIAnalyst
from app.strategy import StrategyEngine, Decision
from app.risk import RiskManager
from app.state import state, EngineStatus, OpenPosition
from app.db import db
from app.logging_setup import get_logger

logger = get_logger("engine")


class TradingEngine:
    def __init__(self):
        self.data_exchange = DataExchange()
        self.execution_exchange = ExecutionExchange()
        self.analyst = AIAnalyst()
        self.strategy = StrategyEngine(self.analyst)
        self.risk = RiskManager()
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()  # set = paused
        self._last_evaluated_candle_ts: dict[str, int] = {}

    def request_stop(self):
        self._stop_event.set()

    def pause(self):
        self._pause_event.set()

    def resume(self):
        self._pause_event.clear()

    def halt(self, reason: str):
        """Emergency stop: distinct from pause — requires a code deploy / restart to clear."""
        self._pause_event.set()
        state.halt_reason = reason
        state.status = EngineStatus.HALTED
        logger.critical(f"ENGINE HALTED: {reason}")

    async def _get_usdt_equity(self) -> float:
        try:
            balance = await self.execution_exchange.fetch_balance()
            total = balance.get("total", {})
            usdt = float(total.get("USDT", 0.0))
            if usdt > 0:
                return usdt
        except Exception as e:
            logger.warning(f"Could not fetch Binance balance ({e}), falling back to DB realized PnL + base equity.")
        
        try:
            pnl = await db.total_realized_pnl()
            return round(10000.0 + pnl, 2)
        except Exception:
            return 10000.0


    async def _bootstrap_daily_risk_state(self):
        """Restore the daily-loss circuit breaker's state from the DB so a
        restart mid-day doesn't reset an already-spent loss budget."""
        try:
            day_start_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
            realized_today = await db.realized_pnl_since(day_start_iso)
            day_start_equity = await db.earliest_equity_today(day_start_iso)
            if day_start_equity is None:
                day_start_equity = await self._get_usdt_equity()
            self.risk.bootstrap_daily_state(day_start_equity, realized_today)
        except Exception as e:
            logger.warning(f"Could not restore daily risk state from DB, starting fresh: {e}")

    async def _process_symbol(self, symbol: str, equity: float):
        ohlcv = await self.data_exchange.fetch_ohlcv(symbol, settings.timeframe, settings.ohlcv_lookback)

        # Only re-evaluate once per newly-closed candle. Polling faster than
        # the timeframe (e.g. 60s polls on a 15m chart) would otherwise call
        # Gemini repeatedly against the *same* closed candle — since Gemini
        # has nonzero temperature, that's not extra confirmation, it's
        # re-rolling the same confidence-threshold dice against identical
        # data until one roll happens to clear the bar. That inflates false
        # entries and burns API calls for zero informational gain.
        if len(ohlcv) < 2:
            return
        last_closed_ts = ohlcv[-2][0]
        is_new_candle = self._last_evaluated_candle_ts.get(symbol) != last_closed_ts
        self._last_evaluated_candle_ts[symbol] = last_closed_ts

        # Check if we should perform an active market scan evaluation
        recent_count = await db.decision_count_since(symbol, 15)
        if not is_new_candle and recent_count > 0:
            return


        order_book = await self.data_exchange.fetch_order_book(symbol)

        decision: Decision = await self.strategy.evaluate(symbol, ohlcv, order_book)

        ai_action = decision.analyst.decision.action if (decision.analyst and decision.analyst.is_valid) else None
        ai_conf = decision.analyst.decision.confidence_score if (decision.analyst and decision.analyst.is_valid) else None
        ai_reasoning = decision.analyst.decision.reasoning if (decision.analyst and decision.analyst.is_valid) else decision.analyst.error if decision.analyst else None
        technical_bias = decision.technical.bias if decision.technical else None

        if not decision.is_actionable:
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason=decision.reject_reason)
            logger.info(f"[{symbol}] HOLD ({decision.reject_reason})")
            return

        if symbol in state.open_positions:
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="already_have_open_position")
            logger.info(f"[{symbol}] Signal {decision.action} skipped: position already open for this symbol.")
            return

        if self.risk.in_cooldown(symbol):
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="symbol_in_loss_cooldown")
            logger.info(f"[{symbol}] Signal {decision.action} skipped: symbol is in post-loss cooldown.")
            return

        if self.risk.daily_loss_limit_hit(equity):
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="daily_loss_limit_hit")
            return

        # Only LONG is executable on spot without margin/borrow; SHORT signals
        # on a spot-only integration are logged for visibility but not traded.
        if decision.action == "SHORT":
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="short_not_supported_on_spot")
            logger.info(f"[{symbol}] SHORT signal noted but not executed (spot-only integration).")
            return

        # Use a fresh live price for sizing/execution, not the technical
        # snapshot's candle close — that close is from the last *closed*
        # candle, which can be up to one full timeframe old (see
        # indicators.py). Also acts as a sanity check: if live price has
        # gapped hard away from the candle the signal was computed on, the
        # signal is stale and we skip rather than trade on outdated context.
        ticker = await self.data_exchange.fetch_ticker(symbol)
        live_price = float(ticker["last"])
        staleness_pct = abs(live_price - decision.technical.close) / decision.technical.close * 100
        if staleness_pct > settings.max_price_staleness_pct:
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason=f"stale_signal_price_moved_{staleness_pct:.2f}pct")
            logger.info(f"[{symbol}] Rejected: live price diverged {staleness_pct:.2f}% from signal candle — stale signal.")
            return

        plan = self.risk.build_trade_plan(
            symbol=symbol,
            side="buy",
            entry_price=live_price,
            atr=decision.technical.atr,
            available_equity_usd=equity,
            open_position_count=len(state.open_positions),
            confidence_score=ai_conf,
        )
        if plan is None:
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="risk_check_failed")
            return

        if settings.dry_run:
            logger.info(f"[DRY_RUN][{symbol}] Would BUY qty={plan.quantity:.6f} SL={plan.stop_loss:.4f} TP={plan.take_profit:.4f}")
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="dry_run")
            return

        await self._execute_long(symbol, plan, live_price, technical_bias, ai_action, ai_conf, ai_reasoning)

    async def _execute_long(self, symbol, plan, live_price, technical_bias, ai_action, ai_conf, ai_reasoning):
        market = await self.execution_exchange.market_precision(symbol)
        qty = self.execution_exchange.amount_to_precision(symbol, plan.quantity)
        limits = market.get("limits", {})
        min_qty = limits.get("amount", {}).get("min")
        min_cost = limits.get("cost", {}).get("min")
        if min_qty and qty < min_qty:
            logger.info(f"[{symbol}] Rejected: quantity {qty} below exchange minimum {min_qty}.")
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="below_exchange_min_qty")
            return
        if min_cost and qty * live_price < min_cost:
            logger.info(f"[{symbol}] Rejected: notional below exchange minimum cost {min_cost}.")
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="below_exchange_min_cost")
            return

        # Marketable limit (IOC) instead of a blind market order: caps how
        # much worse than the observed price we're willing to pay, so a thin
        # order book can't slip the fill far away from what we sized for.
        limit_price = self.execution_exchange.price_to_precision(symbol, live_price * (1 + settings.max_slippage_pct / 100))
        try:
            order = await self.execution_exchange.create_limit_ioc_order(symbol, "buy", qty, limit_price)
        except OrderRejected as e:
            logger.error(f"[{symbol}] Entry order rejected: {e}")
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason=f"order_rejected: {e}")
            return

        filled_qty = float(order.get("filled") or 0)
        if filled_qty <= 0:
            # IOC couldn't fill within our slippage tolerance — no position
            # was opened, nothing to protect, this is a normal non-event.
            logger.info(f"[{symbol}] Entry IOC order did not fill within slippage tolerance. No position opened.")
            await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=False, reject_reason="ioc_entry_unfilled")
            return

        fill_price = float(order.get("average") or order.get("price") or live_price)
        # Recompute SL/TP off the ACTUAL fill price (may differ from the
        # pre-trade estimate due to slippage), preserving the same distances
        # risk.py calculated, not the pre-trade estimate itself.
        tp_distance = plan.take_profit - plan.entry_price_estimate
        sl_distance = plan.entry_price_estimate - plan.stop_loss
        stop_loss = self.execution_exchange.price_to_precision(symbol, fill_price - sl_distance)
        take_profit = self.execution_exchange.price_to_precision(symbol, fill_price + tp_distance)
        stop_limit_price = self.execution_exchange.price_to_precision(symbol, stop_loss * 0.999)
        qty = self.execution_exchange.amount_to_precision(symbol, filled_qty)

        protection = "none"
        bracket_order_id = None
        try:
            bracket = await self.execution_exchange.create_oco_sell(symbol, qty, take_profit, stop_loss, stop_limit_price)
            bracket_order_id = str(bracket.get("id") or bracket.get("orderListId") or bracket.get("info", {}).get("orderListId") or "")
            protection = "oco"
        except OrderRejected as e:
            logger.error(f"[{symbol}] OCO bracket rejected ({e}). Attempting fallback stop-loss-only order.")
            try:
                fallback = await self.execution_exchange.create_stop_loss_only(symbol, qty, stop_loss, stop_limit_price)
                bracket_order_id = str(fallback.get("id") or "")
                protection = "stop_only"
                logger.warning(f"[{symbol}] Fallback stop-loss placed (no automatic take-profit leg).")
            except OrderRejected as e2:
                logger.critical(
                    f"[{symbol}] BUY filled but BOTH OCO and fallback stop-loss FAILED: {e2}. "
                    "Position is UNPROTECTED. Halting new entries — reconciliation will keep "
                    "watching this position and manually close it if SL/TP levels are breached."
                )
                self.halt(f"unprotected_position:{symbol}")

        trade_id = await db.log_trade(
            symbol=symbol, side="buy", quantity=qty, entry_price=fill_price,
            stop_loss=stop_loss, take_profit=take_profit, notional_usd=qty * fill_price,
            order_id=str(order.get("id", "")), bracket_order_id=bracket_order_id,
        )
        await db.log_decision(symbol, technical_bias, ai_action, ai_conf, ai_reasoning, executed=True)

        async with state.lock():
            state.open_positions[symbol] = OpenPosition(
                symbol=symbol, side="buy", quantity=qty, entry_price=fill_price,
                stop_loss=stop_loss, take_profit=take_profit,
                opened_at=datetime.now(timezone.utc).isoformat(),
                trade_id=trade_id, order_id=str(order.get("id", "")),
                bracket_order_id=bracket_order_id, protection=protection,
            )
        logger.info(f"[{symbol}] EXECUTED BUY qty={qty} @ ~{fill_price} SL={stop_loss} TP={take_profit} protection={protection}")

    async def _close_position(self, symbol: str, pos: OpenPosition, exit_price: float, reason: str):
        pnl = (exit_price - pos.entry_price) * pos.quantity
        self.risk.record_realized_pnl(pnl)
        if pnl < 0:
            self.risk.mark_loss(symbol)
        await db.close_trade(pos.trade_id, pnl)
        async with state.lock():
            state.open_positions.pop(symbol, None)
        logger.info(f"[{symbol}] Position closed ({reason}). PnL: {pnl:.2f} USDT")

    async def _reconcile_open_positions(self):
        """
        Runs every cycle regardless of pause/halt state — monitoring and
        protecting existing risk must never stop just because new entries
        have been paused.
        """
        for symbol, pos in list(state.open_positions.items()):
            try:
                if pos.protection in ("oco", "stop_only") and pos.bracket_order_id:
                    open_orders = await self.execution_exchange.fetch_open_orders(symbol)
                    still_open = any(
                        str(o.get("id")) == pos.bracket_order_id
                        or str(o.get("orderListId", "")) == pos.bracket_order_id
                        or str(o.get("info", {}).get("orderListId", "")) == pos.bracket_order_id
                        for o in open_orders
                    )
                    if still_open:
                        continue

                    # Bracket order is no longer open -> filled. Get the real
                    # exit price from trade history rather than guessing off
                    # the current ticker (which may have moved since the fill).
                    exit_price = await self._actual_exit_price(symbol, pos)
                    await self._close_position(symbol, pos, exit_price, reason=f"{pos.protection}_bracket_filled")

                else:
                    # No exchange-side protection at all (both OCO and
                    # fallback failed at entry). We cannot infer closure from
                    # "no open orders" here since there never was one — the
                    # engine itself must watch price and close manually.
                    ticker = await self.data_exchange.fetch_ticker(symbol)
                    last = float(ticker["last"])
                    if last <= pos.stop_loss or last >= pos.take_profit:
                        try:
                            order = await self.execution_exchange.create_market_order(symbol, "sell", pos.quantity)
                            exit_price = float(order.get("average") or last)
                            await self._close_position(symbol, pos, exit_price, reason="manual_watch_close")
                        except OrderRejected as e:
                            logger.critical(f"[{symbol}] Manual protective close FAILED: {e}. Still unprotected — needs urgent manual intervention.")
            except Exception as e:
                logger.warning(f"[{symbol}] Reconciliation error: {e}")
                continue

    async def _actual_exit_price(self, symbol: str, pos) -> float:
        """Best-effort real fill price from trade history; falls back to
        current ticker price if trade history is unavailable."""
        try:
            since_ms = None
            trades = await self.execution_exchange.fetch_my_trades(symbol, since=since_ms, limit=20)
            relevant = [t for t in trades if t.get("side") == "sell"]
            if relevant:
                relevant = relevant[-3:]  # most recent fills
                total_cost = sum(float(t["price"]) * float(t["amount"]) for t in relevant)
                total_qty = sum(float(t["amount"]) for t in relevant)
                if total_qty > 0:
                    return total_cost / total_qty
        except Exception as e:
            logger.warning(f"[{symbol}] Could not fetch trade history for exit price, falling back to ticker: {e}")
        ticker = await self.data_exchange.fetch_ticker(symbol)
        return float(ticker["last"])

    async def run(self):
        state.status = EngineStatus.RUNNING
        logger.info(
            f"Engine starting. DataExchange={settings.data_exchange_id} ExecutionExchange={settings.execution_exchange_id} "
            f"Testnet={settings.binance_testnet} DryRun={settings.dry_run} "
            f"Pairs={settings.trading_pairs} Poll={settings.poll_interval_seconds}s"
        )
        await db.init()

        # Startup can fail transiently (exchange briefly unreachable, DNS
        # hiccup, etc). Retry with backoff instead of letting one bad moment
        # permanently kill the 24/7 task — but still respect a stop request.
        backoff = 5
        while not self._stop_event.is_set():
            try:
                await self.data_exchange.load_markets()
                await self.execution_exchange.load_markets()
                break
            except Exception as e:
                logger.error(f"Startup: failed to load exchange markets ({e}). Retrying in {backoff}s.")
                state.status = EngineStatus.ERROR
                state.last_error = f"startup: {e}"
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=backoff)
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, 120)

        if not self._stop_event.is_set():
            await self._bootstrap_daily_risk_state()

        while not self._stop_event.is_set():
            is_paused_or_halted = self._pause_event.is_set()
            state.status = EngineStatus.HALTED if state.halt_reason else (
                EngineStatus.PAUSED if is_paused_or_halted else EngineStatus.RUNNING
            )

            cycle_start = datetime.now(timezone.utc)
            try:
                equity = await self._get_usdt_equity()
                async with state.lock():
                    state.last_equity_usd = equity
                await db.snapshot_equity(equity)

                # Monitoring/protecting existing positions runs UNCONDITIONALLY,
                # even paused or halted — a halt must stop new risk, never stop
                # watching risk that already exists.
                await self._reconcile_open_positions()

                if settings.trading_enabled and not is_paused_or_halted:
                    for symbol in settings.trading_pairs:
                        if self._stop_event.is_set() or self._pause_event.is_set():
                            break
                        try:
                            await self._process_symbol(symbol, equity)
                        except Exception as e:
                            logger.exception(f"[{symbol}] Unhandled error during processing cycle: {e}")
                            state.last_error = f"{symbol}: {e}"

                state.cycles_completed += 1
                state.last_cycle_at = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.exception(f"Unhandled error in engine cycle: {e}")
                state.last_error = str(e)
                if not state.halt_reason:
                    state.status = EngineStatus.ERROR

            elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            # Poll faster while paused/halted so an unprotected position (if
            # any) is checked and protected quickly rather than waiting a
            # full normal cycle.
            base_interval = 10 if is_paused_or_halted else settings.poll_interval_seconds
            sleep_for = max(1.0, base_interval - elapsed)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                pass

        logger.info("Engine loop stopped.")
