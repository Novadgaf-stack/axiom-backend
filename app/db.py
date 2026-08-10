"""
Lightweight SQLite persistence. Purpose: survive process restarts (Render
redeploys, crashes) without losing the daily-loss counter, trade history, or
decision audit trail. This is not a high-throughput datastore — it's an
audit log and monitoring backing store, which is exactly what this needs to be.
"""
import os
import aiosqlite
from datetime import datetime, timezone

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    technical_bias TEXT,
    ai_action TEXT,
    ai_confidence INTEGER,
    ai_reasoning TEXT,
    executed INTEGER NOT NULL DEFAULT 0,
    reject_reason TEXT
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    notional_usd REAL,
    order_id TEXT,
    bracket_order_id TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    realized_pnl_usd REAL
);

CREATE TABLE IF NOT EXISTS equity_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    equity_usd REAL NOT NULL
);
"""


class Database:
    def __init__(self, path: str = None):
        self.path = path or settings.database_path
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def log_decision(self, symbol, technical_bias, ai_action, ai_confidence, ai_reasoning, executed, reject_reason=None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO decisions (ts, symbol, technical_bias, ai_action, ai_confidence, ai_reasoning, executed, reject_reason) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    symbol, technical_bias, ai_action, ai_confidence, ai_reasoning,
                    int(executed), reject_reason,
                ),
            )
            await db.commit()

    async def log_trade(self, symbol, side, quantity, entry_price, stop_loss, take_profit, notional_usd, order_id, bracket_order_id=None):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO trades (ts, symbol, side, quantity, entry_price, stop_loss, take_profit, notional_usd, order_id, bracket_order_id, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')",
                (
                    datetime.now(timezone.utc).isoformat(),
                    symbol, side, quantity, entry_price, stop_loss, take_profit, notional_usd, order_id, bracket_order_id,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def close_trade(self, trade_id: int, realized_pnl_usd: float):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE trades SET status='closed', realized_pnl_usd=? WHERE id=?",
                (realized_pnl_usd, trade_id),
            )
            await db.commit()

    async def snapshot_equity(self, equity_usd: float):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO equity_snapshots (ts, equity_usd) VALUES (?, ?)",
                (datetime.now(timezone.utc).isoformat(), equity_usd),
            )
            await db.commit()

    async def recent_trades(self, limit: int = 50):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def recent_decisions(self, limit: int = 50):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def equity_curve(self, limit: int = 500):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM equity_snapshots ORDER BY id DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return list(reversed([dict(r) for r in rows]))

    async def realized_pnl_since(self, since_iso: str) -> float:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(realized_pnl_usd), 0) FROM trades WHERE status='closed' AND ts >= ?",
                (since_iso,),
            )
            row = await cursor.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0

    async def earliest_equity_today(self, since_iso: str) -> float | None:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT equity_usd FROM equity_snapshots WHERE ts >= ? ORDER BY id ASC LIMIT 1",
                (since_iso,),
            )
            row = await cursor.fetchone()
            return float(row[0]) if row else None


db = Database()
