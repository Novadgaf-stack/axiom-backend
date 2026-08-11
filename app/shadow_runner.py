"""
NEXUS-7 — SHADOW OPERATIONS MODULE (PHASE 1)
Runs live market candle feeds through standard strategies and central risk validation,
logging hypothetical orders and tracking performance without submitting trades to exchange venues.
"""
import time
from typing import Dict, List, Optional
from app.audit_log import ImmutableAuditLogger
from app.risk import RiskManager, TradePlan
from app.state_machine import TradingStateMachine, EngineState
from app.logging_setup import get_logger

logger = get_logger("shadow_runner")


class ShadowOperationsRunner:
    """Manages Phase 1 Shadow Operations on live market data."""
    def __init__(self, audit_logger: Optional[ImmutableAuditLogger] = None):
        self.state_machine = TradingStateMachine(initial_state=EngineState.STARTING)
        self.risk_manager = RiskManager()
        self.audit_logger = audit_logger or ImmutableAuditLogger(log_path="./logs/shadow_operations.jsonl", environment="SHADOW")
        
        self.start_time = time.time()
        self.hypothetical_trades: List[Dict] = []
        self.missed_signals: List[Dict] = []
        self.total_signals_evaluated = 0
        self.successful_shadow_orders = 0
        
        # Transition state machine
        self.state_machine.transition_to(EngineState.HEALTH_CHECK, reason="Shadow runner init")
        self.state_machine.transition_to(EngineState.READY, reason="Shadow health check pass")
        self.state_machine.transition_to(EngineState.TRADING, reason="Start Shadow Operations")

    def process_shadow_bar(
        self,
        symbol: str,
        price: float,
        atr: float,
        signal_direction: str,  # "BUY", "SELL", or "HOLD"
        confidence_score: int,
        equity_usd: float = 10000.0
    ) -> Optional[Dict]:
        """
        Evaluates a market candle through the central risk engine in Shadow Mode.
        """
        self.total_signals_evaluated += 1
        
        if signal_direction not in ("BUY", "SELL") or confidence_score < 90:
            return None
            
        side = signal_direction.lower()
        open_positions = len(self.hypothetical_trades)
        
        # Validate order risk through central authoritative risk engine
        approved, reject_reason, plan = self.risk_manager.validate_order_risk(
            symbol=symbol,
            side=side,
            entry_price=price,
            atr=atr,
            available_equity_usd=equity_usd,
            open_position_count=open_positions,
            confidence_score=confidence_score,
            trading_allowed=self.state_machine.can_trade()
        )
        
        if not approved or plan is None:
            missed_record = {
                "symbol": symbol,
                "side": side,
                "price": price,
                "reason": reject_reason or "Risk rejection",
                "timestamp": time.time()
            }
            self.missed_signals.append(missed_record)
            logger.info(f"[SHADOW REJECTED BY RISK]: {symbol} {side.upper()} | Reason: {reject_reason}")
            return None
            
        self.successful_shadow_orders += 1
        
        trade_record = {
            "trade_id": f"shadow_{self.successful_shadow_orders}",
            "symbol": symbol,
            "side": side,
            "entry_price": price,
            "quantity": plan.quantity,
            "stop_loss": plan.stop_loss,
            "take_profit": plan.take_profit,
            "notional_usd": plan.notional_usd,
            "risk_usd": plan.risk_usd,
            "confidence_score": confidence_score,
            "timestamp": time.time(),
            "environment": "SHADOW",
            "status": "OPEN"
        }
        
        self.hypothetical_trades.append(trade_record)
        
        self.audit_logger.log_event(
            event_type="SHADOW_TRADE_OPENED",
            symbol=symbol,
            details=trade_record
        )
        
        logger.info(
            f"[SHADOW TRADE EXECUTED]: {symbol} {side.upper()} qty={plan.quantity:.6f} @ ${price:,.2f} | "
            f"SL=${plan.stop_loss:,.2f} TP=${plan.take_profit:,.2f} Notional=${plan.notional_usd:,.2f}"
        )
        return trade_record

    def get_operational_metrics(self) -> Dict:
        uptime_sec = time.time() - self.start_time
        return {
            "environment": "SHADOW",
            "uptime_sec": round(uptime_sec, 2),
            "state": self.state_machine.state_name,
            "total_signals_evaluated": self.total_signals_evaluated,
            "successful_shadow_orders": self.successful_shadow_orders,
            "missed_signals_count": len(self.missed_signals),
            "open_shadow_positions": len([t for t in self.hypothetical_trades if t.get("status") == "OPEN"])
        }
