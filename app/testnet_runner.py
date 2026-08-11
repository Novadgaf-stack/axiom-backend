"""
NEXUS-7 — TESTNET EXECUTION MODULE (PHASE 2)
Manages the end-to-end execution loop on Binance Testnet venue with continuous reconciliation and audit logging.
"""
import time
from typing import Dict, List, Optional
from app.audit_log import ImmutableAuditLogger
from app.order_idempotency import generate_client_order_id, OrderIdempotencyManager
from app.reconciliation import StateReconciler
from app.risk import RiskManager
from app.state_machine import TradingStateMachine, EngineState
from app.watchdog import ServiceWatchdog
from app.logging_setup import get_logger

logger = get_logger("testnet_runner")


class TestnetExecutionRunner:
    """Manages Phase 2 Testnet execution and lifecycle tracking."""
    def __init__(self, audit_logger: Optional[ImmutableAuditLogger] = None):
        self.state_machine = TradingStateMachine(initial_state=EngineState.STARTING)
        self.risk_manager = RiskManager()
        self.reconciler = StateReconciler(self.state_machine)
        self.watchdog = ServiceWatchdog(self.state_machine)
        self.idempotency_mgr = OrderIdempotencyManager()
        self.audit_logger = audit_logger or ImmutableAuditLogger(log_path="./logs/testnet_operations.jsonl", environment="TESTNET")
        
        self.start_time = time.time()
        self.active_positions: Dict[str, Dict] = {}
        self.active_orders: Dict[str, Dict] = {}
        self.order_history: List[Dict] = []
        self.reconciliation_incidents: List[Dict] = []
        self.total_orders_submitted = 0
        self.total_orders_filled = 0
        self.duplicate_orders_count = 0
        
        # Transition state machine to TRADING
        self.state_machine.transition_to(EngineState.HEALTH_CHECK, reason="Testnet init")
        self.state_machine.transition_to(EngineState.READY, reason="Testnet startup check pass")
        self.state_machine.transition_to(EngineState.TRADING, reason="Start Testnet Execution")

    def execute_testnet_signal(
        self,
        symbol: str,
        price: float,
        atr: float,
        signal_direction: str,
        confidence_score: int,
        bar_index: int,
        equity_usd: float = 10000.0,
        mock_venue_submit_fn = None
    ) -> Optional[Dict]:
        """
        Full End-to-End Testnet Execution Loop:
        Signal -> Risk Gate -> Idempotency -> Venue Order -> Fill -> Position -> Reconciliation -> Audit Log
        """
        self.watchdog.record_heartbeat("market_data")
        self.watchdog.record_heartbeat("strategy_engine")
        
        if signal_direction not in ("BUY", "SELL") or confidence_score < 90:
            return None
            
        side = signal_direction.lower()
        
        # Check Central Risk Engine
        approved, reject_reason, plan = self.risk_manager.validate_order_risk(
            symbol=symbol,
            side=side,
            entry_price=price,
            atr=atr,
            available_equity_usd=equity_usd,
            open_position_count=len(self.active_positions),
            confidence_score=confidence_score,
            trading_allowed=self.state_machine.can_trade()
        )
        
        if not approved or plan is None:
            logger.info(f"[TESTNET RISK REJECTION]: {symbol} {side.upper()} | Reason: {reject_reason}")
            return None

        # Generate Deterministic Idempotent Client Order ID
        ts_ms = int(time.time() * 1000)
        cid = generate_client_order_id(symbol, side, bar_index, ts_ms)
        
        if cid in self.active_orders:
            self.duplicate_orders_count += 1
            logger.error(f"DUPLICATE ORDER BLOCKED BY IDEMPOTENCY ENGINE: {cid}")
            return None
            
        # Register order in idempotency manager
        order_record = self.idempotency_mgr.register_order(cid, symbol, side, price, plan.quantity)
        self.active_orders[cid] = order_record
        self.total_orders_submitted += 1
        
        self.audit_logger.log_event(
            event_type="TESTNET_ORDER_SUBMITTED",
            symbol=symbol,
            details=order_record
        )
        
        # Execute venue submission
        if mock_venue_submit_fn:
            venue_res = mock_venue_submit_fn(cid, symbol, side, price, plan.quantity)
        else:
            # Standard venue response simulation
            venue_res = {"status": "FILLED", "order_id": f"v_{cid}", "filled_qty": plan.quantity, "avg_price": price}
            
        status = venue_res.get("status", "FILLED")
        if status == "FILLED":
            order_record["status"] = "FILLED"
            self.total_orders_filled += 1
            
            # Position Lifecycle
            pos_record = {
                "symbol": symbol,
                "side": side,
                "entry_price": price,
                "quantity": plan.quantity,
                "stop_loss": plan.stop_loss,
                "take_profit": plan.take_profit,
                "order_id": cid,
                "opened_at": time.time(),
                "status": "OPEN"
            }
            self.active_positions[symbol] = pos_record
            self.order_history.append(order_record)
            
            self.audit_logger.log_event(
                event_type="TESTNET_POSITION_OPENED",
                symbol=symbol,
                details=pos_record
            )
            
            logger.info(
                f"[TESTNET ORDER FILLED]: {symbol} {side.upper()} qty={plan.quantity:.6f} @ ${price:,.2f} | "
                f"SL=${plan.stop_loss:,.2f} TP=${plan.take_profit:,.2f}"
            )
            return pos_record
            
        return order_record

    def run_reconciliation_check(self, exchange_positions: Dict[str, float], exchange_orders: List[str]) -> Dict:
        """Runs periodic exchange state reconciliation against venue."""
        self.watchdog.record_heartbeat("exchange_api")
        self.watchdog.record_heartbeat("risk_engine")
        
        local_pos = {sym: pos["quantity"] for sym, pos in self.active_positions.items()}
        local_ords = list(self.active_orders.keys())
        
        rec_res = self.reconciler.reconcile(local_pos, exchange_positions, local_ords, exchange_orders)
        if not rec_res["is_synced"]:
            self.reconciliation_incidents.append(rec_res)
            self.audit_logger.log_event("RECONCILIATION_MISMATCH", "GLOBAL", rec_res)
            
        return rec_res

    def get_testnet_metrics(self) -> Dict:
        uptime = time.time() - self.start_time
        return {
            "environment": "TESTNET",
            "uptime_sec": round(uptime, 2),
            "engine_state": self.state_machine.state_name,
            "total_orders_submitted": self.total_orders_submitted,
            "total_orders_filled": self.total_orders_filled,
            "duplicate_orders_count": self.duplicate_orders_count,
            "reconciliation_incidents": len(self.reconciliation_incidents),
            "active_positions_count": len(self.active_positions),
            "trading_allowed": self.state_machine.can_trade()
        }
