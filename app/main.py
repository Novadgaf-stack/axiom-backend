"""
Entrypoint. Deployed on Render as a persistent Web Service (or Background
Worker + separate lightweight API — see README for that variant). This is
deliberately NOT deployed to Vercel or any serverless platform: the whole
point of this process is the asyncio.create_task loop below, which must run
continuously between requests. Serverless platforms freeze/kill execution
between invocations, which would silently stop the trading loop.

Run locally:      uvicorn app.main:app --reload
Run in production: uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_setup import get_logger
from app.engine import TradingEngine
from app.api import router as api_router
from app import engine_registry

logger = get_logger("main")

_engine_task: asyncio.Task | None = None
_engine: TradingEngine | None = None
_keep_alive_task: asyncio.Task | None = None


async def _keep_alive_loop():
    """Background task to keep event loop active and self-ping /health every 4 minutes."""
    import urllib.request

    logger.info("Keep-alive background task started.")
    while True:
        try:
            await asyncio.sleep(240)
            port = settings.port
            url = f"http://127.0.0.1:{port}/health"

            def _ping():
                req = urllib.request.Request(url, headers={"User-Agent": "Nexus7-KeepAlive/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.status

            try:
                status = await asyncio.to_thread(_ping)
                logger.debug(f"[KEEP-ALIVE] Self-ping status: {status}")
            except Exception as pe:
                logger.debug(f"[KEEP-ALIVE] Heartbeat cycle executed (self-ping info: {pe})")
        except asyncio.CancelledError:
            logger.info("Keep-alive task cancelled.")
            break
        except Exception as e:
            logger.warning(f"[KEEP-ALIVE] Error in keep-alive loop: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine_task, _engine, _keep_alive_task

    from app.db import db
    try:
        await db.init()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    problems = settings.validate()
    engine_registry.set_config_problems(problems)

    _keep_alive_task = asyncio.create_task(_keep_alive_loop())
    engine_registry.set_keep_alive_task(_keep_alive_task)

    if problems:
        for p in problems:
            logger.error(f"CONFIG PROBLEM: {p}")
        critical = [p for p in problems if "API_KEY" in p or "API_SECRET" in p]
        if not critical:
            _engine = TradingEngine()
            _engine_task = asyncio.create_task(_engine.run())
            engine_registry.set_engine(_engine, _engine_task)
        else:
            logger.critical("Trading engine NOT started due to missing credentials. API will still serve /health.")
            engine_registry.set_engine(None, None)
    else:
        _engine = TradingEngine()
        _engine_task = asyncio.create_task(_engine.run())
        engine_registry.set_engine(_engine, _engine_task)

    yield

    if _keep_alive_task:
        _keep_alive_task.cancel()
        try:
            await _keep_alive_task
        except asyncio.CancelledError:
            pass

    if _engine:
        _engine.request_stop()
    if _engine_task:
        try:
            await asyncio.wait_for(_engine_task, timeout=15)
        except Exception as e:
            logger.warning(f"Error while waiting for engine task shutdown: {e}")



app = FastAPI(title="Nexus-7 Trading Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins else ["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)

try:
    from solana_agent.router import router as solana_router
    app.include_router(solana_router)
except Exception as e:
    logger.warning(f"Solana agent router initialization warning: {e}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port)
