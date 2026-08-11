"""
NEXUS-7 — HEARTBEAT & SERVICE WATCHDOG
Monitors sub-system health and enforces fail-closed behavior on service staleness.
"""
import time
from typing import Dict
from app.state_machine import TradingStateMachine, EngineState
from app.logging_setup import get_logger

logger = get_logger("watchdog")


class ServiceWatchdog:
    """Sub-system Heartbeat & Health Watchdog."""
    def __init__(self, state_machine: TradingStateMachine, stale_threshold_sec: float = 15.0):
        self.state_machine = state_machine
        self.stale_threshold_sec = stale_threshold_sec
        self.heartbeats: Dict[str, float] = {
            "market_data": time.time(),
            "exchange_api": time.time(),
            "strategy_engine": time.time(),
            "risk_engine": time.time(),
            "database": time.time(),
        }

    def record_heartbeat(self, service_name: str):
        """Updates the timestamp of a service heartbeat."""
        self.heartbeats[service_name] = time.time()

    def check_health(self) -> Dict:
        """
        Verifies all service heartbeats. If any are stale, transitions engine to DEGRADED or HALTED.
        """
        now = time.time()
        stale_services = []
        
        for name, ts in self.heartbeats.items():
            age = now - ts
            if age > self.stale_threshold_sec:
                stale_services.append((name, round(age, 2)))
                
        is_healthy = len(stale_services) == 0
        
        if not is_healthy:
            logger.warning(f"HEARTBEAT WATCHDOG DETECTED STALE SERVICES: {stale_services}")
            if self.state_machine.current_state == EngineState.TRADING:
                self.state_machine.transition_to(EngineState.DEGRADED, reason=f"Stale heartbeats: {stale_services}")
                
        return {
            "is_healthy": is_healthy,
            "stale_services": stale_services,
            "heartbeats_age_sec": {name: round(now - ts, 2) for name, ts in self.heartbeats.items()}
        }
