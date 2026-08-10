"""Performance metrics computed from a list of closed simulated trades."""
from dataclasses import dataclass, field


@dataclass
class SimTrade:
    symbol: str
    entry_index: int
    entry_time_ms: int
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    risk_usd: float
    ai_confidence: int | None = None
    exit_index: int | None = None
    exit_time_ms: int | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    fees_usd: float = 0.0
    pnl_usd: float | None = None

    @property
    def r_multiple(self) -> float:
        if not self.risk_usd:
            return 0.0
        return self.pnl_usd / self.risk_usd


@dataclass
class BacktestReport:
    mode: str
    symbol: str
    timeframe: str
    total_candles: int
    initial_equity: float
    final_equity: float
    net_pnl_usd: float
    net_pnl_pct: float
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    expectancy_usd: float
    expectancy_r: float
    avg_win_usd: float
    avg_loss_usd: float
    max_drawdown_pct: float
    max_consecutive_losses: int
    total_fees_usd: float
    ai_calls_made: int
    trades: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)  # list of (timestamp_ms, equity)

    def print_summary(self):
        print("=" * 62)
        print(f"BACKTEST REPORT — mode={self.mode}  symbol={self.symbol}  tf={self.timeframe}")
        print("=" * 62)
        print(f"  Candles processed:        {self.total_candles}")
        print(f"  Initial equity:           ${self.initial_equity:,.2f}")
        print(f"  Final equity:             ${self.final_equity:,.2f}")
        print(f"  Net PnL:                  ${self.net_pnl_usd:,.2f}  ({self.net_pnl_pct:+.2f}%)")
        print(f"  Total fees paid:          ${self.total_fees_usd:,.2f}")
        print("-" * 62)
        print(f"  Total trades:             {self.total_trades}")
        print(f"  Win rate:                 {self.win_rate_pct:.2f}%")
        print(f"  Profit factor:            {self.profit_factor:.2f}")
        print(f"  Expectancy per trade:     ${self.expectancy_usd:,.2f}  ({self.expectancy_r:+.2f}R)")
        print(f"  Avg win / avg loss:       ${self.avg_win_usd:,.2f} / ${self.avg_loss_usd:,.2f}")
        print(f"  Max drawdown:             {self.max_drawdown_pct:.2f}%")
        print(f"  Max consecutive losses:   {self.max_consecutive_losses}")
        print(f"  AI analyst calls made:    {self.ai_calls_made}")
        print("=" * 62)


def compute_report(
    trades: list[SimTrade],
    initial_equity: float,
    mode: str,
    symbol: str,
    timeframe: str,
    total_candles: int,
    ai_calls_made: int,
) -> BacktestReport:
    n = len(trades)
    wins = [t for t in trades if t.pnl_usd is not None and t.pnl_usd > 0]
    losses = [t for t in trades if t.pnl_usd is not None and t.pnl_usd <= 0]

    gross_profit = sum(t.pnl_usd for t in wins)
    gross_loss = -sum(t.pnl_usd for t in losses)  # positive magnitude
    total_fees = sum(t.fees_usd for t in trades)
    net_pnl = sum(t.pnl_usd for t in trades)

    win_rate = (len(wins) / n * 100) if n else 0.0
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float("inf") if gross_profit > 0 else 0.0

    avg_win = (gross_profit / len(wins)) if wins else 0.0
    avg_loss = (-gross_loss / len(losses)) if losses else 0.0  # negative number for display
    expectancy_usd = (net_pnl / n) if n else 0.0
    avg_risk = (sum(t.risk_usd for t in trades) / n) if n else 0.0
    expectancy_r = (expectancy_usd / avg_risk) if avg_risk else 0.0

    # Equity curve + max drawdown, stepping through trades in chronological order
    equity = initial_equity
    peak = initial_equity
    max_dd = 0.0
    equity_curve = [(trades[0].entry_time_ms if trades else 0, initial_equity)]
    consecutive_losses = 0
    max_consecutive_losses = 0

    for t in sorted(trades, key=lambda x: x.exit_index or 0):
        equity += t.pnl_usd
        equity_curve.append((t.exit_time_ms, equity))
        peak = max(peak, equity)
        dd = ((peak - equity) / peak * 100) if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
        if t.pnl_usd <= 0:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0

    final_equity = initial_equity + net_pnl
    net_pnl_pct = (net_pnl / initial_equity * 100) if initial_equity else 0.0

    return BacktestReport(
        mode=mode,
        symbol=symbol,
        timeframe=timeframe,
        total_candles=total_candles,
        initial_equity=initial_equity,
        final_equity=final_equity,
        net_pnl_usd=net_pnl,
        net_pnl_pct=net_pnl_pct,
        total_trades=n,
        win_rate_pct=win_rate,
        profit_factor=profit_factor,
        expectancy_usd=expectancy_usd,
        expectancy_r=expectancy_r,
        avg_win_usd=avg_win,
        avg_loss_usd=avg_loss,
        max_drawdown_pct=max_dd,
        max_consecutive_losses=max_consecutive_losses,
        total_fees_usd=total_fees,
        ai_calls_made=ai_calls_made,
        trades=trades,
        equity_curve=equity_curve,
    )
