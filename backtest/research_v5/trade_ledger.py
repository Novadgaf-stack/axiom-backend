"""
NEXUS-7 — CANONICAL AUDITABLE TRADE LEDGER (RESEARCH V5)
Defines unified TradeRecord and TradeLedger classes for auditable PnL and metric accounting.
"""
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class TradeRecord:
    timestamp_iso: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    holding_bars: int
    exit_reason: str
    gross_pnl_usd: float
    fee_usd: float
    slippage_usd: float
    net_pnl_usd: float
    r_multiple: float

    def to_dict(self) -> Dict:
        return asdict(self)


class TradeLedger:
    """Canonical trade ledger for consistent, auditable metrics calculation across all V5 modules."""

    def __init__(self, initial_equity: float = 10_000.0):
        self.initial_equity = initial_equity
        self.records: List[TradeRecord] = []

    def add_trade(self, record: TradeRecord):
        self.records.append(record)

    def calculate_summary(self) -> Dict:

        trades_count = len(self.records)

        if trades_count == 0:
            return {
                "trades_count": 0,
                "win_rate": None,  # N/A
                "profit_factor": None,  # NaN / N/A
                "net_pnl_usd": 0.0,
                "gross_pnl_usd": 0.0,
                "total_fees_usd": 0.0,
                "total_slippage_usd": 0.0,
                "expectancy_usd": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": None,
            }

        wins = [r for r in self.records if r.net_pnl_usd > 0]
        losses = [r for r in self.records if r.net_pnl_usd < 0]

        gross_profit = sum(r.net_pnl_usd for r in wins)
        gross_loss = abs(sum(r.net_pnl_usd for r in losses))

        win_rate = (len(wins) / trades_count) * 100.0

        if gross_loss == 0:
            profit_factor = 99.0 if gross_profit > 0 else None
        else:
            profit_factor = gross_profit / gross_loss

        net_pnl_usd = sum(r.net_pnl_usd for r in self.records)
        gross_pnl_usd = sum(r.gross_pnl_usd for r in self.records)
        total_fees_usd = sum(r.fee_usd for r in self.records)
        total_slippage_usd = sum(r.slippage_usd for r in self.records)
        expectancy_usd = net_pnl_usd / trades_count

        # Compute drawdown curve
        equity = self.initial_equity
        peak = equity
        max_dd = 0.0

        for r in self.records:
            equity += r.net_pnl_usd
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

        return {
            "trades_count": trades_count,
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
            "net_pnl_usd": round(net_pnl_usd, 2),
            "gross_pnl_usd": round(gross_pnl_usd, 2),
            "total_fees_usd": round(total_fees_usd, 2),
            "total_slippage_usd": round(total_slippage_usd, 2),
            "expectancy_usd": round(expectancy_usd, 2),
            "max_drawdown_pct": round(max_dd, 1),
        }
