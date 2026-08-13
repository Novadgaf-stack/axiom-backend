"""
FastAPI Router for Solana Agent Layer (/api/solana/*).
"""
import uuid
from typing import List, Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from solana_agent.config import solana_settings
from solana_agent.policy_gate import policy_gate
from solana_agent.rpc_simulator import rpc_simulator
from solana_agent.solana_client import solana_client
from solana_agent.schemas import SolanaAgentDecision, ExecutionResult
from app.api import require_auth

router = APIRouter(prefix="/api/solana", tags=["solana-agent"])

_decision_history: List[Dict] = []


class EvaluateSignalRequest(BaseModel):
    symbol: str = "SOL/USDT"
    action: str = "EXECUTE_DEVNET_SWAP"  # "EXECUTE_DEVNET_SWAP" | "AUDIT_COMMIT"
    sol_amount: float = 0.05
    confidence_score: float = 88.0
    reasoning: str = "EMA trend bullish & AI confidence threshold cleared"


@router.get("/status", dependencies=[Depends(require_auth)])
@router.get("/health", dependencies=[Depends(require_auth)])
async def get_solana_status():
    problems = solana_settings.validate()
    return {
        "status": "ok" if not problems else "degraded",
        "cluster": solana_settings.solana_cluster,
        "rpc_url": solana_settings.solana_rpc_url,
        "wallet_public_key": solana_client.public_key_str,
        "max_sol_per_tx": solana_settings.max_sol_per_tx,
        "max_tx_per_hour": solana_settings.max_tx_per_hour,
        "min_confidence_floor": solana_settings.min_confidence_floor,
        "config_problems": problems,
    }


@router.post("/evaluate", dependencies=[Depends(require_auth)])
async def evaluate_signal(req: EvaluateSignalRequest):
    """
    Evaluates signal through deterministic policy gate, simulates on Devnet RPC,
    and executes Devnet tx if policy & simulation pass.
    """
    decision_id = f"SOL-DEV-{uuid.uuid4().hex[:12].upper()}"

    # Step 1: Policy Gate Check
    policy_res = policy_gate.evaluate_policy(
        sol_amount=req.sol_amount,
        confidence_score=req.confidence_score,
    )

    if not policy_res.passed:
        result = SolanaAgentDecision(
            decision_id=decision_id,
            symbol=req.symbol,
            action="HOLD",
            sol_amount=req.sol_amount,
            confidence_score=req.confidence_score,
            reasoning=f"REJECTED BY POLICY GATE: {policy_res.rejection_reason}",
            policy_check=policy_res,
            simulation=await rpc_simulator.simulate_tx(),
            execution=ExecutionResult(status="REJECTED", cluster="devnet"),
        )
        _decision_history.append(result.model_dump())
        return result

    # Step 2: Transaction Pre-flight Simulation
    sim_res = await rpc_simulator.simulate_tx()
    if not sim_res.success:
        result = SolanaAgentDecision(
            decision_id=decision_id,
            symbol=req.symbol,
            action="HOLD",
            sol_amount=req.sol_amount,
            confidence_score=req.confidence_score,
            reasoning=f"REJECTED BY RPC SIMULATOR: {sim_res.error}",
            policy_check=policy_res,
            simulation=sim_res,
            execution=ExecutionResult(status="FAILED", cluster="devnet"),
        )
        _decision_history.append(result.model_dump())
        return result

    # Step 3: Isolated Devnet Keypair Signing & Execution
    exec_res = await solana_client.execute_devnet_transaction(
        sol_amount=req.sol_amount,
        memo_text=f"{decision_id} | {req.symbol} | {req.reasoning}",
    )
    policy_gate.record_execution()

    result = SolanaAgentDecision(
        decision_id=decision_id,
        symbol=req.symbol,
        action=req.action,
        sol_amount=req.sol_amount,
        confidence_score=req.confidence_score,
        reasoning=req.reasoning,
        policy_check=policy_res,
        simulation=sim_res,
        execution=exec_res,
    )
    _decision_history.append(result.model_dump())
    return result


@router.get("/history", dependencies=[Depends(require_auth)])
async def get_history(limit: int = 50):
    return _decision_history[-min(limit, 200):]
