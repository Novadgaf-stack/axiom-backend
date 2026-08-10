"""
The event-driven replay loop. Deliberately imports and reuses the exact
production modules (indicators.compute_snapshot, strategy.StrategyEngine,
risk.RiskManager) rather than reimplementing their logic — the whole point
of this harness is to test what the live engine actually does, not a
paraphrase of it that could drift out of sync.

Look-ahead discipline: at simulated "now" = candle i, only candles[0..i] are
known. indicators.compute_snapshot always drops its own last input row
(treating it as the still-forming candle — see indicators.py), so we hand it
candles[0..i] plus one throwaway placeholder row, exactly mirroring what the
live engine passes at the same point in time. The strategy is evaluated on
that closed information only; if it decides to enter, the fill is simulated
at the OPEN of candle i+1 (the next candle), never at candle i's own close —
you cannot actually trade at the price the signal was generated from.
"""
import asyncio
from datetime import datetime, timezone

from app.indicators import compute_snapshot
from app.risk import RiskManager, TradePlan
from app.strategy import StrategyEngine

from backtest.metrics import SimTrade
from backtest.mock_ai_analyst import synthetic_order_book_summary


def _ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


class BacktestSimulator:
    def __init__(
        self,
        candles: list,
        symbol: str,
        analyst,
        settings_obj,
        initial_equity: float = 10_000.0,
        fee_pct: float = 0.1,
        slippage_pct: float = 0.05,
        max_hold_bars: int = 96,
        same_bar_conflict: str = "conservative",  # "conservative" -> SL wins; "optimistic" -> TP wins
    ):
        self.candles = candles
        self.symbol = symbol
        self.settings = settings_obj
        self.strategy = StrategyEngine(analyst)
        self.risk = RiskManager()
        self.initial_equity = initial_equity
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.max_hold_bars = max_hold_bars
        self.same_bar_conflict = same_bar_conflict
        self.min_lookback = max(30, self.settings.atr_period + 5) + 1

    def _window(self, i: int) -> list:
        """Candles known as of the close of candle i, plus a throwaway
        placeholder so compute_snapshot's drop-last-row convention lines up
        exactly with what the live engine does — see module docstring."""
        return self.candles[: i + 1] + [self.candles[i]]

    async def run(self) -> list[SimTrade]:
        trades: list[SimTrade] = []
        equity = self.initial_equity
        i = self.min_lookback

        while i < len(self.candles) - 1:
            candle = self.candles[i]
            now = _ms_to_dt(candle[0])

            window = self._window(i)
            snapshot = compute_snapshot(
                window, atr_period=self.settings.atr_period, min_volume_ratio=self.settings.min_volume_ratio
            )
            if snapshot is None:
                i += 1
                continue

            if self.risk.in_cooldown(self.symbol, now=now):
                i += 1
                continue
            if self.risk.daily_loss_limit_hit(equity, now=now):
                i += 1
                continue

            order_book = synthetic_order_book_summary(candle)
            decision = await self.strategy.evaluate(self.symbol, window, order_book)

            if not decision.is_actionable or decision.action != "LONG":
                # Spot-only, matching production: SHORT signals aren't traded.
                i += 1
                continue

            entry_index = i + 1
            if entry_index >= len(self.candles):
                break

            plan = self.risk.build_trade_plan(
                symbol=self.symbol,
                side="buy",
                entry_price=self.candles[entry_index][1],  # next candle's open
                atr=snapshot.atr,
                available_equity_usd=equity,
                open_position_count=0,
            )
            if plan is None:
                i += 1
                continue

            trade, exit_index = self._simulate_trade(plan, entry_index)
            trades.append(trade)
            equity += trade.pnl_usd
            self.risk.record_realized_pnl(trade.pnl_usd)
            if trade.pnl_usd <= 0:
                self.risk.mark_loss(self.symbol, now=_ms_to_dt(trade.exit_time_ms))

            i = exit_index + 1

        return trades

    def _simulate_trade(self, plan: TradePlan, entry_index: int) -> tuple[SimTrade, int]:
        entry_price = plan.entry_price_estimate * (1 + self.slippage_pct / 100)
        entry_fee = entry_price * plan.quantity * (self.fee_pct / 100)

        trade = SimTrade(
            symbol=self.symbol,
            entry_index=entry_index,
            entry_time_ms=self.candles[entry_index][0],
            entry_price=entry_price,
            quantity=plan.quantity,
            stop_loss=plan.stop_loss,
            take_profit=plan.take_profit,
            risk_usd=plan.risk_usd,
        )

        last_scan_index = min(len(self.candles) - 1, entry_index + self.max_hold_bars)
        exit_index = None
        exit_price = None
        exit_reason = None

        for j in range(entry_index + 1, last_scan_index + 1):
            _, o, h, l, c, v = self.candles[j]
            hit_sl = l <= plan.stop_loss
            hit_tp = h >= plan.take_profit

            if hit_sl and hit_tp:
                # Can't know intrabar path from OHLCV alone. Default is the
                # PESSIMISTIC assumption (stop hit first) so the backtest
                # doesn't flatter itself on ambiguous bars — flip via
                # same_bar_conflict="optimistic" if you want the other bound.
                if self.same_bar_conflict == "optimistic":
                    exit_index, exit_price, exit_reason = j, plan.take_profit, "take_profit_same_bar_ambiguous"
                else:
                    exit_index, exit_price, exit_reason = j, plan.stop_loss, "stop_loss_same_bar_ambiguous"
                break
            elif hit_sl:
                exit_index, exit_price, exit_reason = j, plan.stop_loss, "stop_loss"
                break
            elif hit_tp:
                exit_index, exit_price, exit_reason = j, plan.take_profit, "take_profit"
                break

        if exit_index is None:
            exit_index = last_scan_index
            exit_price = self.candles[exit_index][4]  # close of final scanned bar
            exit_reason = "timeout"

        exit_price_with_slippage = exit_price * (1 - self.slippage_pct / 100)
        exit_fee = exit_price_with_slippage * plan.quantity * (self.fee_pct / 100)

        gross_pnl = (exit_price_with_slippage - entry_price) * plan.quantity
        fees = entry_fee + exit_fee
        net_pnl = gross_pnl - fees

        trade.exit_index = exit_index
        trade.exit_time_ms = self.candles[exit_index][0]
        trade.exit_price = exit_price_with_slippage
        trade.exit_reason = exit_reason
        trade.fees_usd = fees
        trade.pnl_usd = net_pnl

        return trade, exit_index


def run_backtest_sync(*args, **kwargs) -> list[SimTrade]:
    """Convenience sync wrapper — the loop is entirely CPU/mock-bound for
    the mock AI modes, so there's no real benefit to async at the CLI level;
    only ai_live mode does real I/O, and it awaits normally inside run()."""
    sim = BacktestSimulator(*args, **kwargs)
    return asyncio.run(sim.run())
