"""
NEXUS-7 — INCIDENT MANAGEMENT SYSTEM (PHASE 10)
Assigns sequential incident IDs (INC-2026-XXXXXX), logs structured operational records,
and automatically halts the state machine on CRITICAL incidents.
"""
import json
import os
import time
from typing import Dict, Optional, List
from app.state_machine import TradingStateMachine, EngineState
from app.logging_setup import get_logger

logger = get_logger("incident_logger")


class IncidentManager:
    """Manages operational incidents and automatic safety halts."""
    def __init__(self, state_machine: Optional[TradingStateMachine] = None, log_path: str = "testnet_incidents.jsonl"):
        self.state_machine = state_machine
        self.log_path = log_path
        self.incident_counter = 0
        self.incidents_history: List[Dict] = []
        
        # Initialize log file
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                pass  # create empty file

    def log_incident(
        self,
        component: str,
        event: str,
        severity: str,  # "INFO", "WARNING", "ERROR", "CRITICAL"
        state_before: str,
        state_after: str,
        action_taken: str,
        recovery_status: str,
        details: Optional[Dict] = None
    ) -> Dict:
        """Logs a structured incident record and triggers state machine halt if CRITICAL."""
        self.incident_counter += 1
        year = time.strftime("%Y", time.gmtime())
        incident_id = f"INC-{year}-{self.incident_counter:06d}"
        
        incident_record = {
            "incident_id": incident_id,
            "timestamp": time.time(),
            "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "component": component,
            "event": event,
            "severity": severity.upper(),
            "state_before": state_before,
            "state_after": state_after,
            "action_taken": action_taken,
            "recovery_status": recovery_status,
            "details": details or {}
        }
        
        self.incidents_history.append(incident_record)
        
        # Write to JSONL file
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(incident_record) + "\n")
            
        logger.info(f"[INCIDENT {incident_id}] [{severity.upper()}] Component: {component} | Event: {event} | Action: {action_taken}")
        
        # Auto-halt on CRITICAL
        if severity.upper() == "CRITICAL" and self.state_machine:
            if self.state_machine.current_state not in (EngineState.HALTED, EngineState.HALTING):
                logger.critical(f"CRITICAL INCIDENT {incident_id} ENCOUNTERED -> HALTING TRADING ENGINE")
                self.state_machine.transition_to(EngineState.HALTED, reason=f"Critical incident: {incident_id}")
                
        return incident_record

    def get_summary(self) -> Dict:
        total = len(self.incidents_history)
        critical_count = len([i for i in self.incidents_history if i["severity"] == "CRITICAL"])
        error_count = len([i for i in self.incidents_history if i["severity"] == "ERROR"])
        warning_count = len([i for i in self.incidents_history if i["severity"] == "WARNING"])
        return {
            "total_incidents": total,
            "critical_incidents": critical_count,
            "error_incidents": error_count,
            "warning_incidents": warning_count,
            "log_path": self.log_path
        }
