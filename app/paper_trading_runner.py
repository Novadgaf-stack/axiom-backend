"""
NEXUS-7 — FORWARD PAPER TRADING EXECUTION SAFETY LAYER
Runs zero-risk simulated order execution with tiny risk sizing (0.5% max risk per trade),
hard daily loss circuit breakers (2.0% max daily loss), and paper PnL telemetry.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("paper_trading")


class PaperTradingRunner:

    def __init__(
        self,
        initial_equity: float = 10000.0,
        risk_pct_per_trade: float = 0.005,
        max_daily_drawdown_pct: float = 0.02,
        log_file: str = "./logs/paper_trading.log",
    ):
        self.equity = initial_equity
        self.initial_equity = initial_equity
        self.peak_equity = initial_equity
        self.risk_pct_per_trade = risk_pct_per_trade
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.log_file = log_file

        self.daily_start_equity = initial_equity
        self.circuit_breaker_active = False
        self.open_positions: List[Dict] = []
        self.completed_trades: List[Dict] = []

        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self._init_logger()

    def _init_logger(self):
        handler = logging.FileHandler(self.log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | paper | %(message)s"))
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    def reset_daily_window(self):
        self.daily_start_equity = self.equity
        self.circuit_breaker_active = False
        logger.info(f"Daily paper window reset. Start equity: ${self.daily_start_equity:,.2f}")

    def check_circuit_breaker(self) -> bool:
        if self.daily_start_equity <= 0:
            return False
        daily_loss_pct = (self.daily_start_equity - self.equity) / self.daily_start_equity
        if daily_loss_pct >= self.max_daily_drawdown_pct:
            self.circuit_breaker_active = True
            logger.warning(f"CIRCUIT BREAKER TRIGGERED: Daily loss {daily_loss_pct * 100:.2f}% >= {self.max_daily_drawdown_pct * 100:.1f}%. Execution locked.")
            return True
        return False

    def execute_paper_order(
        self,
        symbol: str,
        side: str,
        price: float,
        stop_loss: float,
        take_profit: float,
        confidence_score: int,
        adx: float,
    ) -> Optional[Dict]:
        if self.circuit_breaker_active or self.check_circuit_breaker():
            logger.warning(f"Paper order rejected for {symbol}: Circuit breaker active.")
            return None

        if confidence_score < 92 or adx < 28.0:
            logger.info(f"Paper order rejected for {symbol}: High-confidence criteria not met (Conf={confidence_score}, ADX={adx:.1f}).")
            return None

        # Tiny Risk Sizing (0.5% max risk)
        risk_amount = self.equity * self.risk_pct_per_trade
        price_risk = abs(price - stop_loss)
        if price_risk <= 0:
            return None
        position_qty = risk_amount / price_risk

        order = {
            "order_id": f"PAPER-{len(self.completed_trades) + len(self.open_positions) + 1:04d}",
            "symbol": symbol,
            "side": side,
            "entry_price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_qty": position_qty,
            "risk_usd": risk_amount,
            "confidence_score": confidence_score,
            "adx": adx,
            "entry_time": datetime.now(timezone.utc).isoformat(),
            "status": "OPEN",
        }
        self.open_positions.append(order)
        logger.info(f"Paper order executed: {order['order_id']} {side} {symbol} Qty={position_qty:.4f} @ ${price:.2f} (Risk=${risk_amount:.2f})")
        return order

    def close_paper_position(self, order_id: str, exit_price: float, exit_reason: str) -> Optional[Dict]:
        pos = next((p for p in self.open_positions if p["order_id"] == order_id), None)
        if not pos:
            return None

        self.open_positions.remove(pos)
        if pos["side"] == "BUY":
            pnl_usd = (exit_price - pos["entry_price"]) * pos["position_qty"]
        else:
            pnl_usd = (pos["entry_price"] - exit_price) * pos["position_qty"]

        # Friction (0.15% roundtrip fee + slippage)
        friction = pos["entry_price"] * pos["position_qty"] * 0.0015
        net_pnl = pnl_usd - friction

        self.equity += net_pnl
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity

        pos.update({
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "net_pnl_usd": net_pnl,
            "exit_time": datetime.now(timezone.utc).isoformat(),
            "status": "CLOSED",
        })
        self.completed_trades.append(pos)
        self.check_circuit_breaker()

        logger.info(f"Paper position closed: {order_id} @ ${exit_price:.2f} ({exit_reason}) Net PnL: ${net_pnl:+.2f} New Equity: ${self.equity:,.2f}")
        return pos

    def get_telemetry(self) -> Dict:
        net_pnl = self.equity - self.initial_equity
        win_trades = [t for t in self.completed_trades if t["net_pnl_usd"] > 0]
        win_rate = (len(win_trades) / len(self.completed_trades) * 100.0) if self.completed_trades else 0.0
        return {
            "equity": round(self.equity, 2),
            "net_pnl_usd": round(net_pnl, 2),
            "total_paper_trades": len(self.completed_trades),
            "win_rate_pct": round(win_rate, 1),
            "circuit_breaker_active": self.circuit_breaker_active,
            "open_positions_count": len(self.open_positions),
        }
