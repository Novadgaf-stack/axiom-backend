"""
NEXUS-7 — SHADOW MODE EXECUTION HANDLER
Evaluates real market data and signals through the Central Risk Engine without placing real orders.
"""
import time
from typing import Dict, List
from app.audit_log import ImmutableAuditLogger
from app.logging_setup import get_logger

logger = get_logger("shadow_mode")


class ShadowModeEngine:
    """Executes Shadow Mode hypothetical trade logging."""
    def __init__(self, audit_logger: ImmutableAuditLogger):
        self.audit_logger = audit_logger
        self.hypothetical_positions: List[Dict] = []

    def evaluate_shadow_trade(
        self,
        symbol: str,
        side: str,
        price: float,
        qty: float,
        stop_loss: float,
        take_profit: float,
        signal_reason: str
    ) -> Dict:
        """
        Logs a hypothetical shadow order that passed all risk checks.
        """
        shadow_record = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": qty,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "signal_reason": signal_reason,
            "timestamp": time.time(),
            "status": "HYPOTHETICAL_FILLED",
            "environment": "SHADOW"
        }
        
        self.hypothetical_positions.append(shadow_record)
        
        self.audit_logger.log_event(
            event_type="SHADOW_ORDER_PLACED",
            symbol=symbol,
            details=shadow_record
        )
        
        logger.info(f"[SHADOW ORDER LOGGED]: {symbol} {side.upper()} qty={qty} @ ${price:,.2f} | Reason: {signal_reason}")
        return shadow_record
