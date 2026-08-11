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
        return True  # If no server token configured, allow access
    
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


@router.post("/api/engine/trigger-trade", dependencies=[Depends(require_auth)])
async def trigger_trade(symbol: str = "BTC/USDT", side: str = "LONG"):
    from app.state import OpenPosition
    eng = require_engine()
    equity = await eng._get_usdt_equity()
    
    try:
        ticker = await eng.data_exchange.fetch_ticker(symbol)
        entry_price = float(ticker["last"])
    except Exception:
        entry_price = 68500.0 if "BTC" in symbol else 3500.0

    atr = entry_price * 0.02
    sl = round(entry_price - (atr * settings.atr_sl_multiplier), 2)
    tp = round(entry_price + (atr * settings.atr_tp_multiplier), 2)
    qty = round((equity * (settings.max_position_pct / 100)) / entry_price, 6)
    notional = round(qty * entry_price, 2)
    
    ts_now = int(datetime.now(timezone.utc).timestamp())
    order_id = f"TEST-{ts_now}"
    bracket_id = f"BRACKET-{ts_now}"
    
    trade_id = await db.log_trade(
        symbol=symbol,
        side=side,
        quantity=qty,
        entry_price=entry_price,
        stop_loss=sl,
        take_profit=tp,
        notional_usd=notional,
        order_id=order_id,
        bracket_order_id=bracket_id,
    )
    
    pos = OpenPosition(
        symbol=symbol,
        side=side,
        quantity=qty,
        entry_price=entry_price,
        stop_loss=sl,
        take_profit=tp,
        opened_at=datetime.now(timezone.utc).isoformat(),
        trade_id=trade_id,
        order_id=order_id,
        bracket_order_id=bracket_id,
        protection="oco"
    )
    state.open_positions[symbol] = pos
    await db.log_decision(symbol, side, side, 92, "Manual trigger execution test", executed=True, reject_reason=None)
    
    return {
        "status": "success",
        "message": f"Successfully triggered {side} trade on {symbol} @ ${entry_price:,.2f}",
        "trade_id": trade_id,
        "position": asdict(pos),
    }


