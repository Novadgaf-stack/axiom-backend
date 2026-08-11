"""
NEXUS-7 — STRATEGY PAPER METRICS AUDITOR (PHASE 9)
Independently tracks strategy performance (hypothetical PnL, win rate, expectancy, fees, slippage,
missed trades, execution deviations) during Testnet operation.
"""
from typing import Dict, List, Optional
from app.logging_setup import get_logger

logger = get_logger("paper_metrics")


class PaperPerformanceAuditor:
    """Tracks strategy hypothetical performance independently from execution infrastructure."""
    def __init__(self):
        self.signals_count = 0
        self.hypothetical_trades: List[Dict] = []
        self.missed_trades_count = 0
        self.execution_deviations: List[Dict] = []
        
        self.wins = 0
        self.losses = 0
        self.total_gross_profit = 0.0
        self.total_gross_loss = 0.0
        self.total_fees_usd = 0.0
        self.total_slippage_usd = 0.0

    def record_signal(self, symbol: str, side: str, price: float, confidence_score: int):
        self.signals_count += 1

    def record_paper_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        fee_usd: float = 0.50,
        slippage_usd: float = 0.20
    ) -> Dict:
        """Records completed hypothetical trade and computes paper PnL."""
        pnl_raw = (exit_price - entry_price) * quantity if side.lower() == "buy" else (entry_price - exit_price) * quantity
        pnl_net = pnl_raw - fee_usd - slippage_usd
        
        if pnl_net > 0:
            self.wins += 1
            self.total_gross_profit += pnl_net
        else:
            self.losses += 1
            self.total_gross_loss += abs(pnl_net)
            
        self.total_fees_usd += fee_usd
        self.total_slippage_usd += slippage_usd
        
        trade_record = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "pnl_raw": pnl_raw,
            "pnl_net": pnl_net,
            "fee_usd": fee_usd,
            "slippage_usd": slippage_usd,
            "is_win": pnl_net > 0
        }
        
        self.hypothetical_trades.append(trade_record)
        return trade_record

    def record_missed_trade(self, symbol: str, side: str, reason: str):
        self.missed_trades_count += 1

    def record_execution_deviation(self, symbol: str, expected_price: float, actual_price: float):
        deviation = abs(actual_price - expected_price)
        self.execution_deviations.append({
            "symbol": symbol,
            "expected": expected_price,
            "actual": actual_price,
            "deviation_usd": deviation
        })

    def get_summary(self) -> Dict:
        total_trades = len(self.hypothetical_trades)
        net_pnl = self.total_gross_profit - self.total_gross_loss
        win_rate = (self.wins / total_trades * 100.0) if total_trades > 0 else 0.0
        expectancy = (net_pnl / total_trades) if total_trades > 0 else 0.0
        profit_factor = (self.total_gross_profit / self.total_gross_loss) if self.total_gross_loss > 0 else (99.0 if self.total_gross_profit > 0 else 0.0)
        
        return {
            "signals_evaluated": self.signals_count,
            "hypothetical_trades_count": total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate_pct": round(win_rate, 2),
            "net_pnl_usd": round(net_pnl, 2),
            "expectancy_usd": round(expectancy, 2),
            "profit_factor": round(profit_factor, 2),
            "total_fees_usd": round(self.total_fees_usd, 2),
            "total_slippage_usd": round(self.total_slippage_usd, 2),
            "missed_trades_count": self.missed_trades_count,
            "execution_deviations_count": len(self.execution_deviations),
            "quant_edge_verdict": "NOT PROVEN"
        }
