import secrets
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone

from app.config import settings
from app.state import state
from app.db import db
from app import engine_registry


router = APIRouter()
security = HTTPBearer(auto_error=False)


def require_engine():
    if engine_registry.engine is None:
        raise HTTPException(status_code=503, detail="Trading engine is not running (check server startup logs / credentials).")
    return engine_registry.engine


def require_auth(
    request: Request,
    authorization: str = Header(default=""),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    token_configured = settings.ENGINE_TOKEN or settings.api_auth_token
    if not token_configured:
        raise HTTPException(status_code=503, detail="ENGINE_TOKEN / API_AUTH_TOKEN not configured on server.")
    
    token = ""
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif authorization:
        token = authorization.replace("Bearer ", "").strip()
    
    if not token:
        token = (
            request.headers.get("x-api-key")
            or request.headers.get("x-engine-token")
            or request.headers.get("api-key")
            or request.headers.get("engine-token")
            or request.query_params.get("token")
            or request.query_params.get("key")
            or request.query_params.get("api_key")
            or ""
        )
    
    if token and secrets.compare_digest(token, token_configured):
        return True
    raise HTTPException(status_code=401, detail="Invalid or missing bearer token.")


@router.get("/health")
async def health():
    """Unauthenticated liveness check for Render's health checker / load balancer."""
    return {"status": "ok"}


@router.get("/api/status", dependencies=[Depends(require_auth)])
async def get_status():
    eq = state.last_equity_usd if state.last_equity_usd is not None else 10000.0
    daily_pnl = await db.realized_pnl_since(datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00"))
    total_pnl = await db.total_realized_pnl()
    
    return {
        "status": state.status.value,
        "started_at": state.started_at,
        "last_cycle_at": state.last_cycle_at,
        "cycles_completed": state.cycles_completed,
        "last_error": state.last_error,
        "halt_reason": state.halt_reason,
        "last_equity_usd": eq,
        "last_equity": eq,
        "equity": eq,
        "balance": eq,
        "usdt_balance": eq,
        "total_balance": eq,
        "available_balance": eq,
        "free_balance": eq,
        "used_balance": 0.0,
        "daily_pnl_usd": daily_pnl,
        "total_pnl_usd": total_pnl,
        "open_position_count": len(state.open_positions),
        "config": {
            "testnet": settings.binance_testnet,
            "dry_run": settings.dry_run,
            "trading_enabled": settings.trading_enabled,
            "pairs": settings.trading_pairs,
            "timeframe": settings.timeframe,
            "min_confidence_score": settings.min_confidence_score,
            "poll_interval_seconds": settings.poll_interval_seconds,
            "max_daily_loss_pct": settings.max_daily_loss_pct,
            "max_open_positions": settings.max_open_positions,
            "risk_per_trade_pct": settings.risk_per_trade_pct,
        },
    }


@router.get("/api/balance", dependencies=[Depends(require_auth)])
@router.get("/api/account/balance", dependencies=[Depends(require_auth)])
@router.get("/api/account", dependencies=[Depends(require_auth)])
async def get_balance():
    eq = state.last_equity_usd if state.last_equity_usd is not None else 10000.0
    daily_pnl = await db.realized_pnl_since(datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00"))
    total_pnl = await db.total_realized_pnl()
    return {
        "status": "ok",
        "equity": eq,
        "last_equity_usd": eq,
        "balance": eq,
        "usdt_balance": eq,
        "total_balance": eq,
        "available_balance": eq,
        "free": eq,
        "used": 0.0,
        "daily_pnl_usd": daily_pnl,
        "total_pnl_usd": total_pnl,
        "currency": "USDT",
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

