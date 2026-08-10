"""
In-process shared state between the background trading loop (engine.py) and
the FastAPI monitoring endpoints (api.py). Because both run inside the same
Python process (see main.py), a plain asyncio.Lock-guarded object is
sufficient — no external cache/queue needed for this scale.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class EngineStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    HALTED = "halted"  # kill-switch or daily loss limit
    ERROR = "error"


@dataclass
class OpenPosition:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    opened_at: str
    trade_id: int
    order_id: str
    bracket_order_id: str | None = None
    protection: str = "none"  # "oco" | "stop_only" | "none"


@dataclass
class EngineState:
    status: EngineStatus = EngineStatus.STARTING
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_cycle_at: str | None = None
    last_error: str | None = None
    cycles_completed: int = 0
    open_positions: dict[str, OpenPosition] = field(default_factory=dict)
    last_equity_usd: float | None = None
    halt_reason: str | None = None

    def __post_init__(self):
        self._lock = asyncio.Lock()

    def lock(self):
        return self._lock


state = EngineState()
