"""
Structured Agent Decision Schema for Solana Agent Layer.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class PolicyCheckResult(BaseModel):
    passed: bool
    sol_cap_valid: bool = True
    rate_limit_valid: bool = True
    confidence_valid: bool = True
    rejection_reason: Optional[str] = None


class SimulationResult(BaseModel):
    simulated: bool = False
    success: bool = False
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    status: str = "PENDING"  # "PENDING" | "EXECUTED" | "REJECTED" | "FAILED"
    cluster: str = "devnet"
    tx_signature: Optional[str] = None
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SolanaAgentDecision(BaseModel):
    decision_id: str
    symbol: str
    action: str  # "EXECUTE_DEVNET_SWAP" | "AUDIT_COMMIT" | "HOLD"
    sol_amount: float
    confidence_score: float
    reasoning: str
    policy_check: PolicyCheckResult
    simulation: SimulationResult
    execution: ExecutionResult
