"""
NEXUS-7 — TRADING ENGINE STATE MACHINE
Enforces explicit lifecycle states and strictly validates allowed state transitions.
"""
from enum import Enum, auto
from typing import Set, Dict
import time
from app.logging_setup import get_logger

logger = get_logger("state_machine")


class EngineState(Enum):
    STARTING = "STARTING"
    HEALTH_CHECK = "HEALTH_CHECK"
    READY = "READY"
    TRADING = "TRADING"
    DEGRADED = "DEGRADED"
    HALTING = "HALTING"
    HALTED = "HALTED"
    RECONCILING = "RECONCILING"
    ERROR = "ERROR"


# Valid state transitions
VALID_TRANSITIONS: Dict[EngineState, Set[EngineState]] = {
    EngineState.STARTING: {EngineState.HEALTH_CHECK, EngineState.ERROR, EngineState.HALTED},
    EngineState.HEALTH_CHECK: {EngineState.READY, EngineState.ERROR, EngineState.HALTED},
    EngineState.READY: {EngineState.TRADING, EngineState.DEGRADED, EngineState.HALTING, EngineState.HALTED, EngineState.ERROR},
    EngineState.TRADING: {EngineState.DEGRADED, EngineState.HALTING, EngineState.HALTED, EngineState.RECONCILING, EngineState.ERROR},
    EngineState.DEGRADED: {EngineState.HEALTH_CHECK, EngineState.HALTING, EngineState.HALTED, EngineState.ERROR},
    EngineState.HALTING: {EngineState.HALTED, EngineState.ERROR},
    EngineState.HALTED: {EngineState.RECONCILING, EngineState.HEALTH_CHECK},
    EngineState.RECONCILING: {EngineState.HEALTH_CHECK, EngineState.HALTED, EngineState.ERROR},
    EngineState.ERROR: {EngineState.HALTED, EngineState.RECONCILING},
}


class TradingStateMachine:
    """Manages the operational lifecycle of the Nexus-7 engine."""
    def __init__(self, initial_state: EngineState = EngineState.STARTING):
        self._state = initial_state
        self._last_transition_ts = time.time()
        self._state_history = [(self._state, self._last_transition_ts, "Initial state")]

    @property
    def current_state(self) -> EngineState:
        return self._state

    @property
    def state_name(self) -> str:
        return self._state.value

    def transition_to(self, new_state: EngineState, reason: str = "") -> bool:
        """Attempts to transition to new_state. Returns True if successful, False if invalid."""
        if new_state == self._state:
            return True
            
        allowed = VALID_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            logger.error(f"INVALID STATE TRANSITION REJECTED: {self._state.value} -> {new_state.value} (Reason: {reason})")
            return False
            
        now = time.time()
        logger.info(f"STATE TRANSITION: {self._state.value} -> {new_state.value} | Reason: {reason}")
        self._state = new_state
        self._last_transition_ts = now
        self._state_history.append((new_state, now, reason))
        return True

    def can_trade(self) -> bool:
        """Returns True ONLY when engine is in TRADING state."""
        return self._state == EngineState.TRADING

    def get_history(self) -> list:
        return self._state_history
