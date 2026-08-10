"""Performance metrics computed from a list of closed simulated trades."""
import math
from dataclasses import dataclass, field
import numpy as np


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
    tp1_price: float = 0.0
    tp2_price: float = 0.0
    t1_exit_price: float | None = None
    t2_exit_price: float | None = None
    t1_exit_reason: str | None = None
    t2_exit_reason: str | None = None
    be_triggered: bool = False
    exit_index: int | None = None
    exit_time_ms: int | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    fees_usd: float = 0.0
    slippage_usd: float = 0.0
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
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float
    expectancy_usd: float
    expectancy_r: float
    avg_win_usd: float
    avg_loss_usd: float
    avg_win_r: float
    avg_loss_r: float
    max_drawdown_pct: float
    max_consecutive_losses: int
    longest_recovery_days: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    total_fees_usd: float
    total_slippage_usd: float
    ai_calls_made: int
    trades: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)  # list of (timestamp_ms, equity)

    def print_summary(self):
        print("=" * 66)
        print(f" INSTITUTIONAL BACKTEST REPORT — mode={self.mode} | symbol={self.symbol} | tf={self.timeframe}")
        print("=" * 66)
        print(f"  Candles processed:        {self.total_candles:,}")
        print(f"  Initial equity:           ${self.initial_equity:,.2f}")
        print(f"  Final equity:             ${self.final_equity:,.2f}")
        print(f"  Net PnL:                  ${self.net_pnl_usd:,.2f}  ({self.net_pnl_pct:+.2f}%)")
        print(f"  Total fees paid:          ${self.total_fees_usd:,.2f}")
        print(f"  Total slippage cost:      ${self.total_slippage_usd:,.2f}")
        print("-" * 66)
        print(f"  Total trades:             {self.total_trades} ({self.winning_trades} W / {self.losing_trades} L)")
        print(f"  Win rate:                 {self.win_rate_pct:.2f}%")
        print(f"  Profit factor:            {self.profit_factor:.2f}")
        print(f"  Expectancy per trade:     ${self.expectancy_usd:,.2f}  ({self.expectancy_r:+.2f}R)")
        print(f"  Avg win / avg loss:       ${self.avg_win_usd:,.2f} (+{self.avg_win_r:.2f}R) / ${self.avg_loss_usd:,.2f} ({self.avg_loss_r:.2f}R)")
        print("-" * 66)
        print(f"  Max drawdown:             {self.max_drawdown_pct:.2f}%")
        print(f"  Sharpe ratio (annualized):{self.sharpe_ratio:.2f}")
        print(f"  Sortino ratio:            {self.sortino_ratio:.2f}")
        print(f"  Calmar ratio:             {self.calmar_ratio:.2f}")
        print(f"  Max consecutive losses:   {self.max_consecutive_losses}")
        print(f"  Longest drawdown recovery:{self.longest_recovery_days:.1f} days")
        print(f"  AI analyst calls made:    {self.ai_calls_made}")
        print("=" * 66)


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

    winning_trades = len(wins)
    losing_trades = len(losses)

    gross_profit = sum(t.pnl_usd for t in wins)
    gross_loss = -sum(t.pnl_usd for t in losses)  # positive magnitude
    total_fees = sum(t.fees_usd for t in trades)
    total_slippage = sum(t.slippage_usd for t in trades)
    net_pnl = sum(t.pnl_usd for t in trades)

    win_rate = (winning_trades / n * 100) if n else 0.0
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float("inf") if gross_profit > 0 else 0.0

    avg_win_usd = (gross_profit / winning_trades) if winning_trades else 0.0
    avg_loss_usd = (-gross_loss / losing_trades) if losing_trades else 0.0

    win_r_list = [t.r_multiple for t in wins]
    loss_r_list = [t.r_multiple for t in losses]
    avg_win_r = (sum(win_r_list) / winning_trades) if winning_trades else 0.0
    avg_loss_r = (sum(loss_r_list) / losing_trades) if losing_trades else 0.0

    expectancy_usd = (net_pnl / n) if n else 0.0
    avg_risk = (sum(t.risk_usd for t in trades) / n) if n else 0.0
    expectancy_r = (expectancy_usd / avg_risk) if avg_risk else 0.0

    # Equity curve + drawdown recovery calculation
    equity = initial_equity
    peak = initial_equity
    peak_time_ms = trades[0].entry_time_ms if trades else 0
    max_dd = 0.0
    longest_recovery_ms = 0
    current_dd_start_ms = None

    equity_curve = [(trades[0].entry_time_ms if trades else 0, initial_equity)]
    consecutive_losses = 0
    max_consecutive_losses = 0

    trade_returns = []

    for t in sorted(trades, key=lambda x: x.exit_index or 0):
        prev_eq = equity
        equity += t.pnl_usd
        trade_returns.append(t.pnl_usd / prev_eq if prev_eq > 0 else 0.0)

        t_time = t.exit_time_ms or 0
        equity_curve.append((t_time, equity))

        if equity > peak:
            if current_dd_start_ms is not None:
                rec_ms = t_time - current_dd_start_ms
                longest_recovery_ms = max(longest_recovery_ms, rec_ms)
                current_dd_start_ms = None
            peak = equity
            peak_time_ms = t_time
        else:
            if current_dd_start_ms is None:
                current_dd_start_ms = peak_time_ms
            dd = ((peak - equity) / peak * 100) if peak > 0 else 0.0
            max_dd = max(max_dd, dd)

        if t.pnl_usd <= 0:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0

    if current_dd_start_ms is not None and trades:
        last_t_time = trades[-1].exit_time_ms or 0
        rec_ms = last_t_time - current_dd_start_ms
        longest_recovery_ms = max(longest_recovery_ms, rec_ms)

    longest_recovery_days = longest_recovery_ms / (1000 * 3600 * 24)

    # Annualized Sharpe, Sortino, Calmar
    tf_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}.get(timeframe, 15)
    periods_per_year = (365 * 24 * 60) / tf_minutes
    trades_per_year = (n / total_candles * periods_per_year) if total_candles > 0 else 0.0

    if trade_returns and len(trade_returns) > 1:
        ret_arr = np.array(trade_returns)
        mean_ret = np.mean(ret_arr)
        std_ret = np.std(ret_arr, ddof=1)
        downside_ret = ret_arr[ret_arr < 0]
        std_downside = np.std(downside_ret, ddof=1) if len(downside_ret) > 1 else 1e-9

        sharpe_ratio = (mean_ret / std_ret * math.sqrt(trades_per_year)) if std_ret > 0 else 0.0
        sortino_ratio = (mean_ret / std_downside * math.sqrt(trades_per_year)) if std_downside > 0 else 0.0
    else:
        sharpe_ratio = 0.0
        sortino_ratio = 0.0

    final_equity = initial_equity + net_pnl
    net_pnl_pct = (net_pnl / initial_equity * 100) if initial_equity else 0.0

    years = (total_candles * tf_minutes) / (365.25 * 24 * 60)
    cagr_pct = (((final_equity / initial_equity) ** (1.0 / max(years, 0.01))) - 1) * 100 if final_equity > 0 else 0.0
    calmar_ratio = (cagr_pct / max_dd) if max_dd > 0 else 0.0

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
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate_pct=win_rate,
        profit_factor=profit_factor,
        expectancy_usd=expectancy_usd,
        expectancy_r=expectancy_r,
        avg_win_usd=avg_win_usd,
        avg_loss_usd=avg_loss_usd,
        avg_win_r=avg_win_r,
        avg_loss_r=avg_loss_r,
        max_drawdown_pct=max_dd,
        max_consecutive_losses=max_consecutive_losses,
        longest_recovery_days=longest_recovery_days,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        total_fees_usd=total_fees,
        total_slippage_usd=total_slippage,
        ai_calls_made=ai_calls_made,
        trades=trades,
        equity_curve=equity_curve,
    )
