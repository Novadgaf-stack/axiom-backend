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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine_task, _engine

    problems = settings.validate()
    if problems:
        for p in problems:
            logger.error(f"CONFIG PROBLEM: {p}")
        # We still start the API (so /health and /api/status work for
        # diagnostics) but refuse to start the trading engine if critical
        # secrets are missing.
        critical = [p for p in problems if "API_KEY" in p or "API_SECRET" in p]
        if not critical:
            _engine = TradingEngine()
            engine_registry.set_engine(_engine)
            _engine_task = asyncio.create_task(_engine.run())
        else:
            logger.critical("Trading engine NOT started due to missing credentials. API will still serve /health.")
    else:
        _engine = TradingEngine()
        engine_registry.set_engine(_engine)
        _engine_task = asyncio.create_task(_engine.run())

    yield

    if _engine:
        _engine.request_stop()
    if _engine_task:
        await asyncio.wait_for(_engine_task, timeout=15)


app = FastAPI(title="Nexus-7 Trading Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port)
