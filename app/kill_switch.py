"""
NEXUS-7 — EMERGENCY KILL SWITCH
Provides immediate emergency stop and reset controls that operate independently of AI/strategy components.
"""
import time
from typing import Optional, List, Dict
from app.state_machine import TradingStateMachine, EngineState
from app.logging_setup import get_logger

logger = get_logger("kill_switch")


class EmergencyKillSwitch:
    """Central Emergency Control & Kill Switch Manager."""
    def __init__(self, state_machine: TradingStateMachine):
        self.state_machine = state_machine
        self._is_halted = False
        self._halt_reason = ""
        self._halt_timestamp: Optional[float] = None

    @property
    def is_halted(self) -> bool:
        return self._is_halted or self.state_machine.current_state == EngineState.HALTED

    @property
    def halt_reason(self) -> str:
        return self._halt_reason

    def trigger_emergency_stop(self, reason: str, canceled_orders_count: int = 0) -> Dict:
        """
        Triggers emergency halt sequence:
        1. Disable new entries.
        2. Cancel pending orders.
        3. Enter HALTED state.
        4. Log audit incident.
        """
        self._is_halted = True
        self._halt_reason = reason
        self._halt_timestamp = time.time()
        
        logger.critical(f"[KILL SWITCH] EMERGENCY STOP TRIGGERED: {reason}")
        
        # Transition state machine to HALTING then HALTED
        if self.state_machine.current_state in (EngineState.TRADING, EngineState.READY, EngineState.DEGRADED):
            self.state_machine.transition_to(EngineState.HALTING, reason=f"Kill switch: {reason}")
            self.state_machine.transition_to(EngineState.HALTED, reason="Halt completed")
        else:
            self.state_machine.transition_to(EngineState.HALTED, reason=f"Kill switch forced halt: {reason}")
            
        return {
            "status": "HALTED",
            "reason": reason,
            "timestamp": self._halt_timestamp,
            "canceled_orders": canceled_orders_count,
            "message": "Emergency stop executed successfully. System is HALTED."
        }

    def manual_reset(self, reset_by: str = "operator") -> Dict:
        """
        Manually resets the kill switch and transitions engine from HALTED to RECONCILING then HEALTH_CHECK.
        """
        if not self._is_halted and self.state_machine.current_state != EngineState.HALTED:
            return {"status": "NO_OP", "message": "Engine is not currently halted."}
            
        logger.info(f"MANUAL RESET INITIATED by {reset_by}")
        self._is_halted = False
        self._halt_reason = ""
        self._halt_timestamp = None
        
        self.state_machine.transition_to(EngineState.RECONCILING, reason=f"Manual reset by {reset_by}")
        self.state_machine.transition_to(EngineState.HEALTH_CHECK, reason="Reconciliation complete, starting health check")
        
        return {
            "status": "RESET_SUCCESSFUL",
            "current_state": self.state_machine.state_name,
            "message": "Kill switch reset successfully. Engine moved to HEALTH_CHECK."
        }
