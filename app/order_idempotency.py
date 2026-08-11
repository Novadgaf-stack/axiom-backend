"""
NEXUS-7 — ORDER IDEMPOTENCY & TIMEOUT RECOVERY
Generates deterministic client order IDs and handles execution timeouts safely without duplicate order retries.
"""
import hashlib
import time
from typing import Dict, Optional
from app.logging_setup import get_logger

logger = get_logger("order_idempotency")


def generate_client_order_id(symbol: str, side: str, bar_index: int, timestamp_ms: int) -> str:
    """Generates a unique deterministic client order ID for venue submissions."""
    raw = f"{symbol}_{side}_{bar_index}_{timestamp_ms}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    return f"n7_{symbol.lower()}_{side.lower()}_{bar_index}_{digest}"


class OrderIdempotencyManager:
    """Tracks order request submissions and resolves ambiguous execution timeouts."""
    def __init__(self):
        self.submitted_orders: Dict[str, Dict] = {}

    def register_order(self, client_order_id: str, symbol: str, side: str, price: float, qty: float) -> Dict:
        record = {
            "client_order_id": client_order_id,
            "symbol": symbol,
            "side": side,
            "price": price,
            "qty": qty,
            "status": "SUBMITTED",
            "timestamp": time.time(),
            "retries": 0
        }
        self.submitted_orders[client_order_id] = record
        return record

    def handle_timeout(self, client_order_id: str, venue_query_fn) -> Dict:
        """
        Executed when an order submission times out:
        NEVER blindly retry! Query exchange venue first for client_order_id status.
        """
        logger.warning(f"ORDER TIMEOUT ENCOUNTERED for {client_order_id}. Investigating venue status...")
        
        record = self.submitted_orders.get(client_order_id)
        if not record:
            return {"status": "UNKNOWN", "action": "RECONCILE", "reason": "Order record missing locally"}
            
        # Query exchange for order status
        venue_status = venue_query_fn(client_order_id)
        
        if venue_status.get("exists", False):
            real_status = venue_status.get("status", "FILLED")
            record["status"] = real_status
            logger.info(f"ORDER TIMEOUT RESOLVED: Venue confirms order {client_order_id} exists with status={real_status}")
            return {"status": real_status, "action": "NO_RETRY", "venue_order_id": venue_status.get("order_id")}
        else:
            # Order does not exist on venue, safe to mark rejected or retry
            record["status"] = "REJECTED_ON_VENUE"
            logger.info(f"ORDER TIMEOUT RESOLVED: Venue confirms order {client_order_id} does NOT exist.")
            return {"status": "NOT_ON_VENUE", "action": "SAFE_TO_CANCEL_OR_RETRY"}
