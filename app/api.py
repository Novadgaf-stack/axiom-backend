from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Header

from app.config import settings
from app.state import state
from app.db import db
from app import engine_registry

router = APIRouter()


def require_engine():
    if engine_registry.engine is None:
        raise HTTPException(status_code=503, detail="Trading engine is not running (check server startup logs / credentials).")
    return engine_registry.engine


def require_auth(authorization: str = Header(default="")):
    if not settings.api_auth_token:
        # Fail closed: if no token is configured, control/monitoring endpoints
        # are unavailable rather than silently open.
        raise HTTPException(status_code=503, detail="API_AUTH_TOKEN not configured on server.")
    expected = f"Bearer {settings.api_auth_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token.")
    return True


@router.get("/health")
async def health():
    """Unauthenticated liveness check for Render's health checker / load balancer."""
    return {"status": "ok"}


@router.get("/api/status", dependencies=[Depends(require_auth)])
async def get_status():
    return {
        "status": state.status.value,
        "started_at": state.started_at,
        "last_cycle_at": state.last_cycle_at,
        "cycles_completed": state.cycles_completed,
        "last_error": state.last_error,
        "halt_reason": state.halt_reason,
        "last_equity_usd": state.last_equity_usd,
        "open_position_count": len(state.open_positions),
        "config": {
            "testnet": settings.binance_testnet,
            "dry_run": settings.dry_run,
            "trading_enabled": settings.trading_enabled,
            "pairs": settings.trading_pairs,
            "timeframe": settings.timeframe,
            "min_confidence_score": settings.min_confidence_score,
            "poll_interval_seconds": settings.poll_interval_seconds,
        },
    }


@router.get("/api/positions", dependencies=[Depends(require_auth)])
async def get_positions():
    return {sym: asdict(pos) for sym, pos in state.open_positions.items()}


@router.get("/api/trades", dependencies=[Depends(require_auth)])
async def get_trades(limit: int = 50):
    return await db.recent_trades(limit=min(limit, 500))


@router.get("/api/decisions", dependencies=[Depends(require_auth)])
async def get_decisions(limit: int = 50):
    return await db.recent_decisions(limit=min(limit, 500))


@router.get("/api/equity-curve", dependencies=[Depends(require_auth)])
async def get_equity_curve(limit: int = 500):
    return await db.equity_curve(limit=min(limit, 2000))


@router.post("/api/engine/pause", dependencies=[Depends(require_auth)])
async def pause_engine(engine=Depends(require_engine)):
    engine.pause()
    return {"status": "paused"}


@router.post("/api/engine/resume", dependencies=[Depends(require_auth)])
async def resume_engine(engine=Depends(require_engine)):
    if state.halt_reason:
        raise HTTPException(
            status_code=409,
            detail=f"Engine is HALTED ({state.halt_reason}). Resolve the issue and restart the service to clear a halt.",
        )
    engine.resume()
    return {"status": "resumed"}


@router.post("/api/engine/kill-switch", dependencies=[Depends(require_auth)])
async def kill_switch(engine=Depends(require_engine)):
    engine.halt("manual_kill_switch")
    return {"status": "halted"}
