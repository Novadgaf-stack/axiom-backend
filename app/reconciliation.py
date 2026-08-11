"""
NEXUS-7 — EXCHANGE STATE RECONCILIATION ENGINE
Periodically reconciles local state against exchange API state to prevent state desynchronization.
"""
import time
from typing import Dict, List, Optional
from app.state_machine import TradingStateMachine, EngineState
from app.logging_setup import get_logger

logger = get_logger("reconciliation")


class StateReconciler:
    """Reconciles local engine position & order state with exchange venue API."""
    def __init__(self, state_machine: TradingStateMachine):
        self.state_machine = state_machine
        self._last_reconciliation_ts = 0.0
        self._last_result: Dict = {}

    def reconcile(
        self,
        local_positions: Dict[str, float],
        exchange_positions: Dict[str, float],
        local_orders: List[str],
        exchange_orders: List[str]
    ) -> Dict:
        """
        Compares local vs exchange state. Returns detailed reconciliation report.
        """
        now = time.time()
        self._last_reconciliation_ts = now
        
        position_mismatches = []
        for symbol, local_qty in local_positions.items():
            ex_qty = exchange_positions.get(symbol, 0.0)
            if abs(local_qty - ex_qty) > 1e-6:
                position_mismatches.append({
                    "symbol": symbol,
                    "local_qty": local_qty,
                    "exchange_qty": ex_qty,
                    "diff": round(local_qty - ex_qty, 6)
                })
                
        # Check orders mismatch
        missing_on_exchange = [oid for oid in local_orders if oid not in exchange_orders]
        unexpected_on_exchange = [oid for oid in exchange_orders if oid not in local_orders]
        
        is_synced = len(position_mismatches) == 0 and len(missing_on_exchange) == 0
        
        result = {
            "timestamp": now,
            "is_synced": is_synced,
            "position_mismatches": position_mismatches,
            "missing_orders_on_exchange": missing_on_exchange,
            "unexpected_orders_on_exchange": unexpected_on_exchange,
            "status": "SYNCED" if is_synced else "STATE_MISMATCH"
        }
        self._last_result = result
        
        if not is_synced:
            logger.error(f"EXCHANGE RECONCILIATION MISMATCH DETECTED: {result}")
            if self.state_machine.current_state in (EngineState.TRADING, EngineState.READY):
                self.state_machine.transition_to(EngineState.RECONCILING, reason="Reconciliation mismatch")
        else:
            logger.info("EXCHANGE RECONCILIATION PASSED: Local and venue state perfectly aligned.")
            
        return result

    @property
    def last_result(self) -> Dict:
        return self._last_result
