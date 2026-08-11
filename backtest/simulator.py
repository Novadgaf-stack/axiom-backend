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
import pandas as pd

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
        execution_mode: str = "taker",  # "taker" or "maker"
        enable_4h_trend_filter: bool = False,
        enable_4h_chop_filter: bool = False,
    ):
        self.candles = candles
        self.symbol = symbol
        self.settings = settings_obj
        import app.risk as risk_mod
        import app.strategy as strategy_mod
        risk_mod.settings = self.settings
        strategy_mod.settings = self.settings
        self.strategy = StrategyEngine(analyst)
        self.risk = RiskManager()
        self.initial_equity = initial_equity
        self.execution_mode = execution_mode
        self.unfilled_orders = 0
        if execution_mode == "maker":
            self.fee_pct = 0.02
            self.slippage_pct = 0.00
        else:
            self.fee_pct = fee_pct
            self.slippage_pct = slippage_pct
        self.max_hold_bars = max_hold_bars
        self.same_bar_conflict = same_bar_conflict
        from app.indicators import compute_all_snapshots
        self.df_candles = pd.DataFrame(candles, columns=["ts", "open", "high", "low", "close", "volume"])
        self.snapshots = compute_all_snapshots(
            self.df_candles,
            atr_period=self.settings.atr_period,
            min_volume_ratio=self.settings.min_volume_ratio,
            min_adx=getattr(self.settings, "min_adx", 20.0),
            enable_4h_trend_filter=enable_4h_trend_filter,
            enable_4h_chop_filter=enable_4h_chop_filter,
        )
        self.min_lookback = max(30, self.settings.atr_period + 5) + 1

    def _window(self, i: int):
        """Candles known as of the close of candle i, plus a throwaway
        placeholder so compute_snapshot's drop-last-row convention lines up
        exactly with what the live engine does — see module docstring."""
        return self.df_candles.iloc[: i + 2]

    async def run(self) -> list[SimTrade]:
        trades: list[SimTrade] = []
        equity = self.initial_equity
        i = self.min_lookback

        while i < len(self.candles) - 1:
            candle = self.candles[i]
            now = _ms_to_dt(candle[0])

            snapshot = self.snapshots[i] if i < len(self.snapshots) else None
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
            decision = await self.strategy.evaluate(self.symbol, snapshot, order_book)

            if not decision.is_actionable or decision.action != "LONG":
                # Spot-only, matching production: SHORT signals aren't traded.
                i += 1
                continue

            entry_index = i + 1
            if entry_index >= len(self.candles):
                break

            limit_price = self.candles[entry_index][1]  # Next candle's open price
            filled_index = entry_index

            if self.execution_mode == "maker":
                # Limit order fill uncertainty: check if Low of entry candle or subsequent candle touches limit price
                if self.candles[entry_index][3] <= limit_price:
                    filled_index = entry_index
                elif entry_index + 1 < len(self.candles) and self.candles[entry_index + 1][3] <= limit_price:
                    filled_index = entry_index + 1
                else:
                    self.unfilled_orders += 1
                    i += 1
                    continue

            confidence_score = (
                decision.analyst.decision.confidence_score
                if (decision.analyst and decision.analyst.decision)
                else None
            )

            plan = self.risk.build_trade_plan(
                symbol=self.symbol,
                side="buy",
                entry_price=limit_price,
                atr=snapshot.atr,
                available_equity_usd=equity,
                open_position_count=0,
                confidence_score=confidence_score,
            )
            if plan is None:
                i += 1
                continue

            trade, exit_index = self._simulate_trade(plan, entry_index, confidence_score)
            trades.append(trade)
            equity += trade.pnl_usd
            self.risk.record_realized_pnl(trade.pnl_usd)
            if trade.pnl_usd <= 0:
                self.risk.mark_loss(self.symbol, now=_ms_to_dt(trade.exit_time_ms))

            i = exit_index + 1

        return trades

    def _simulate_trade(self, plan: TradePlan, entry_index: int, confidence_score: int | None = None) -> tuple[SimTrade, int]:
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
            ai_confidence=confidence_score,
        )

        last_scan_index = min(len(self.candles) - 1, entry_index + self.max_hold_bars)
        use_multi_stage = bool(
            getattr(self.settings, "enable_multi_stage_exits", True)
            and getattr(plan, "tp1_price", 0.0) > 0
            and getattr(plan, "tp2_price", 0.0) > 0
        )

        if not use_multi_stage:
            exit_index = None
            exit_price = None
            exit_reason = None
            for j in range(entry_index + 1, last_scan_index + 1):
                _, o, h, l, c, v = self.candles[j]
                hit_sl = l <= plan.stop_loss
                hit_tp = h >= plan.take_profit

                if hit_sl and hit_tp:
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
                exit_price = self.candles[exit_index][4]
                exit_reason = "timeout"

            raw_entry = plan.entry_price_estimate
            entry_slippage_usd = (entry_price - raw_entry) * plan.quantity
            exit_price_net = exit_price * (1 - self.slippage_pct / 100)
            exit_slippage = (exit_price - exit_price_net) * plan.quantity
            exit_fee = exit_price_net * plan.quantity * (self.fee_pct / 100)
            gross_pnl = (exit_price_net - entry_price) * plan.quantity
            fees = entry_fee + exit_fee
            net_pnl = gross_pnl - fees

            trade.exit_index = exit_index
            trade.exit_time_ms = self.candles[exit_index][0]
            trade.exit_price = exit_price_net
            trade.exit_reason = exit_reason
            trade.fees_usd = fees
            trade.slippage_usd = entry_slippage_usd + exit_slippage
            trade.pnl_usd = net_pnl
            return trade, exit_index

        # Multi-stage trade simulation
        qty1 = plan.tranche1_qty if plan.tranche1_qty > 0 else plan.quantity * 0.5
        qty2 = plan.tranche2_qty if plan.tranche2_qty > 0 else plan.quantity * 0.5

        current_sl = plan.stop_loss
        is_t1_hit = False
        t1_exit_price = 0.0
        t1_exit_reason = ""
        t1_exit_idx = None

        t2_exit_price = 0.0
        t2_exit_reason = ""
        t2_exit_idx = None

        for j in range(entry_index + 1, last_scan_index + 1):
            _, o, h, l, c, v = self.candles[j]

            if not is_t1_hit:
                hit_sl1 = l <= current_sl
                hit_tp1 = h >= plan.tp1_price
                if hit_sl1:
                    is_t1_hit = True
                    t1_exit_price = current_sl
                    t1_exit_reason = "stop_loss"
                    t1_exit_idx = j

                    t2_exit_price = current_sl
                    t2_exit_reason = "stop_loss"
                    t2_exit_idx = j
                    break
                elif hit_tp1:
                    is_t1_hit = True
                    t1_exit_price = plan.tp1_price
                    t1_exit_reason = "tp1_scale_out"
                    t1_exit_idx = j
                    current_sl = plan.entry_price_estimate  # Breakeven SL!

            if is_t1_hit and t2_exit_idx is None and (t1_exit_idx is not None and j >= t1_exit_idx):
                hit_sl2 = l <= current_sl
                hit_tp2 = h >= plan.tp2_price
                if hit_sl2:
                    t2_exit_price = current_sl
                    t2_exit_reason = "breakeven_stop_loss" if current_sl >= plan.entry_price_estimate else "stop_loss"
                    t2_exit_idx = j
                    break
                elif hit_tp2:
                    t2_exit_price = plan.tp2_price
                    t2_exit_reason = "tp2_final"
                    t2_exit_idx = j
                    break

        if t1_exit_idx is None:
            t1_exit_idx = last_scan_index
            t1_exit_price = self.candles[last_scan_index][4]
            t1_exit_reason = "timeout"

        if t2_exit_idx is None:
            t2_exit_idx = last_scan_index
            t2_exit_price = self.candles[last_scan_index][4]
            t2_exit_reason = "timeout"

        final_exit_idx = max(t1_exit_idx, t2_exit_idx)

        t1_net_price = t1_exit_price * (1 - self.slippage_pct / 100)
        t1_gross = (t1_net_price - entry_price) * qty1
        t1_fee = (entry_price * qty1 * (self.fee_pct / 100)) + (t1_net_price * qty1 * (self.fee_pct / 100))
        t1_net = t1_gross - t1_fee
        t1_slip = ((entry_price - plan.entry_price_estimate) + (t1_exit_price - t1_net_price)) * qty1

        t2_net_price = t2_exit_price * (1 - self.slippage_pct / 100)
        t2_gross = (t2_net_price - entry_price) * qty2
        t2_fee = (entry_price * qty2 * (self.fee_pct / 100)) + (t2_net_price * qty2 * (self.fee_pct / 100))
        t2_net = t2_gross - t2_fee
        t2_slip = ((entry_price - plan.entry_price_estimate) + (t2_exit_price - t2_net_price)) * qty2

        total_net_pnl = t1_net + t2_net
        total_fees = t1_fee + t2_fee
        total_slip = t1_slip + t2_slip

        effective_exit_price = (t1_net_price * 0.5) + (t2_net_price * 0.5)
        combined_reason = f"T1:{t1_exit_reason}|T2:{t2_exit_reason}"

        trade.exit_index = final_exit_idx
        trade.exit_time_ms = self.candles[final_exit_idx][0]
        trade.exit_price = effective_exit_price
        trade.exit_reason = combined_reason
        trade.fees_usd = total_fees
        trade.slippage_usd = total_slip
        trade.pnl_usd = total_net_pnl

        return trade, final_exit_idx


def run_backtest_sync(*args, **kwargs) -> list[SimTrade]:
    """Convenience sync wrapper — the loop is entirely CPU/mock-bound for
    the mock AI modes, so there's no real benefit to async at the CLI level;
    only ai_live mode does real I/O, and it awaits normally inside run()."""
    sim = BacktestSimulator(*args, **kwargs)
    return asyncio.run(sim.run())
