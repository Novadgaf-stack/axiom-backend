"""
Risk management. Nothing in here is optional or bypassable by the AI layer —
these are hard quantitative rules applied after a decision has already
passed the AI + technical confirmation gate in strategy.py.
"""
from __future__ import annotations
from dataclasses import dataclass

from datetime import datetime, timezone, timedelta

from app.config import settings
from app.logging_setup import get_logger

logger = get_logger("risk")


@dataclass
class TradePlan:
    symbol: str
    side: str  # "buy" or "sell" (spot: buy=open long, sell=close/short-equivalent)
    quantity: float
    entry_price_estimate: float
    stop_loss: float
    take_profit: float
    notional_usd: float
    risk_usd: float
    tp1_price: float = 0.0
    tp2_price: float = 0.0
    tranche1_qty: float = 0.0
    tranche2_qty: float = 0.0

    @property
    def tp1(self) -> float:
        return self.tp1_price

    @property
    def tp2(self) -> float:
        return self.tp2_price


class RiskManager:
    def __init__(self):
        self._daily_start_equity: float | None = None
        self._daily_date: str | None = None
        self._daily_realized_pnl: float = 0.0
        self._cooldown_until: dict[str, datetime] = {}
        from app.drawdown_guard import PortfolioDrawdownGuard
        self.drawdown_guard = PortfolioDrawdownGuard(max_portfolio_dd_pct=15.0)


    def check_portfolio_drawdown(self, current_equity: float) -> bool:
        return self.drawdown_guard.is_circuit_breaker_triggered(current_equity)


    def mark_loss(self, symbol: str, now: datetime = None):
        """Start a cooldown window after a losing trade closes, so the bot
        doesn't immediately re-enter the same setup that just stopped it out
        (a common source of repeated whipsaw losses).

        `now` defaults to the real wall clock for live trading. The
        backtester passes the simulated candle timestamp instead, so a
        year of replayed history rolls cooldowns/days by simulated time,
        not by however long the backtest script actually takes to run.
        """
        now = now or datetime.now(timezone.utc)
        until = now + timedelta(minutes=settings.cooldown_minutes_after_loss)
        self._cooldown_until[symbol] = until
        logger.info(f"[{symbol}] Loss recorded — cooldown until {until.isoformat()}.")

    def in_cooldown(self, symbol: str, now: datetime = None) -> bool:
        now = now or datetime.now(timezone.utc)
        until = self._cooldown_until.get(symbol)
        if until is None:
            return False
        return now < until

    def bootstrap_daily_state(self, day_start_equity: float, realized_pnl_today: float, now: datetime = None):
        """
        Called once at engine startup to restore the daily-loss circuit
        breaker's memory of the current UTC day, so a process restart
        (Render redeploy, crash) doesn't hand the bot a fresh loss budget
        it hasn't earned mid-day.
        """
        now = now or datetime.now(timezone.utc)
        self._daily_date = now.strftime("%Y-%m-%d")
        self._daily_start_equity = day_start_equity
        self._daily_realized_pnl = realized_pnl_today
        logger.info(
            f"Daily risk state restored: start_equity={day_start_equity:.2f} "
            f"realized_pnl_today={realized_pnl_today:.2f}"
        )

    def _roll_day_if_needed(self, current_equity: float, now: datetime = None):
        now = now or datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        if self._daily_date != today:
            self._daily_date = today
            self._daily_start_equity = current_equity
            self._daily_realized_pnl = 0.0
            self.drawdown_guard.reset_daily_peak(current_equity)
            logger.info(f"Daily risk window reset. Start-of-day equity: {current_equity:.2f} USDT")


    def record_realized_pnl(self, pnl_usd: float):
        self._daily_realized_pnl += pnl_usd

    def daily_loss_limit_hit(self, current_equity: float, now: datetime = None) -> bool:
        self._roll_day_if_needed(current_equity, now=now)
        if self._daily_start_equity is None or self._daily_start_equity <= 0:
            return False
        loss_pct = -self._daily_realized_pnl / self._daily_start_equity * 100
        hit = loss_pct >= settings.max_daily_loss_pct
        if hit:
            logger.warning(
                f"Daily loss limit hit: {loss_pct:.2f}% >= {settings.max_daily_loss_pct}%. "
                "New entries blocked until UTC day rolls over."
            )
        return hit

    def build_trade_plan(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        atr: float,
        available_equity_usd: float,
        open_position_count: int,
        confidence_score: int | None = None,
    ) -> TradePlan | None:
        if open_position_count >= settings.max_open_positions:
            logger.info(f"[{symbol}] Rejected: max open positions ({settings.max_open_positions}) reached.")
            return None

        if atr <= 0:
            logger.info(f"[{symbol}] Rejected: ATR is zero/invalid, cannot size stop-loss.")
            return None

        stop_distance = atr * settings.atr_sl_multiplier
        take_profit_distance = atr * settings.atr_tp_multiplier

        t1_mult = getattr(settings, "t1_tp_multiplier", 1.0)
        t2_mult = getattr(settings, "t2_tp_multiplier", 2.5)

        if side == "buy":
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + take_profit_distance
            tp1_price = entry_price + (atr * t1_mult)
            tp2_price = entry_price + (atr * t2_mult)
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - take_profit_distance
            tp1_price = entry_price - (atr * t1_mult)
            tp2_price = entry_price - (atr * t2_mult)

        if stop_loss <= 0:
            logger.info(f"[{symbol}] Rejected: computed stop-loss <= 0.")
            return None

        # Position sizing: dynamic confidence-weighted risk % or baseline settings.risk_per_trade_pct
        risk_pct = settings.risk_per_trade_pct
        if getattr(settings, "confidence_scaling_enabled", True) and confidence_score is not None:
            if confidence_score >= 96:
                risk_pct = 2.0
            elif confidence_score >= 90:
                risk_pct = 1.5
            elif confidence_score >= 85:
                risk_pct = 1.0

        risk_usd = available_equity_usd * (risk_pct / 100)
        quantity = risk_usd / stop_distance

        # Hard cap: notional exposure can't exceed max_position_pct of equity,
        # regardless of what the risk-based sizing above computed. This is the
        # backstop against a too-tight stop producing an oversized position.
        max_notional = available_equity_usd * (settings.max_position_pct / 100)
        notional = quantity * entry_price
        if notional > max_notional:
            quantity = max_notional / entry_price
            notional = quantity * entry_price
            logger.info(f"[{symbol}] Position size capped by MAX_POSITION_PCT to {quantity:.6f}.")

        if notional < settings.min_trade_notional_usd:
            logger.info(f"[{symbol}] Rejected: computed notional ${notional:.2f} is below practical minimum.")
            return None

        tranche1_qty = quantity * 0.5
        tranche2_qty = quantity - tranche1_qty

        return TradePlan(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price_estimate=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            notional_usd=notional,
            risk_usd=risk_usd,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            tranche1_qty=tranche1_qty,
            tranche2_qty=tranche2_qty,
        )

    def validate_order_risk(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        atr: float,
        available_equity_usd: float,
        open_position_count: int,
        confidence_score: int | None = None,
        trading_allowed: bool = True
    ) -> tuple[bool, str | None, TradePlan | None]:
        """
        Single authoritative risk gatekeeper method.
        Validates all quantitative risk limits before any order is created.
        Returns (is_approved, reject_reason, trade_plan).
        """
        if not trading_allowed:
            return False, "TRADING_HALTED_OR_DISABLED", None
            
        if self.daily_loss_limit_hit(available_equity_usd):
            return False, "DAILY_LOSS_LIMIT_REACHED", None

        if self.check_portfolio_drawdown(available_equity_usd):
            return False, "PORTFOLIO_DRAWDOWN_LIMIT_REACHED", None

        if self.in_cooldown(symbol):
            return False, f"COOLDOWN_ACTIVE_FOR_{symbol}", None

            
        plan = self.build_trade_plan(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            atr=atr,
            available_equity_usd=available_equity_usd,
            open_position_count=open_position_count,
            confidence_score=confidence_score
        )
        
        if plan is None:
            return False, "TRADE_PLAN_REJECTED_BY_RISK_LIMITS", None
            
        return True, None, plan

