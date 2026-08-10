"""
Binance Spot exchange wrapper built on ccxt.

Design notes:
- All network calls run through `tenacity` retry with exponential backoff,
  targeted at the specific ccxt exceptions that represent *transient*
  problems (network drop, rate limit, exchange temporarily unavailable).
  Non-transient errors (bad symbol, insufficient funds, invalid order)
  are NOT retried — they're raised immediately so the caller can react.
- ccxt is synchronous by default; every call is offloaded to a thread via
  asyncio.to_thread so it never blocks the event loop running the 24/7 engine.
- Testnet vs mainnet is controlled entirely by settings.binance_testnet.
  There is no code path here that silently trades mainnet.
"""
import asyncio
import logging
import ccxt
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.config import settings
from app.logging_setup import get_logger

logger = get_logger("exchange")

TRANSIENT_ERRORS = (
    ccxt.NetworkError,
    ccxt.ExchangeNotAvailable,
    ccxt.RequestTimeout,
    ccxt.DDoSProtection,
)


class OrderRejected(Exception):
    """Raised for non-transient order failures (bad params, insufficient balance, etc)."""


def _retry_decorator():
    return retry(
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        before_sleep=before_sleep_log(logger, log_level=logging.INFO),
        reraise=True,
    )


class BinanceExchange:
    def __init__(self):
        if not settings.binance_api_key or not settings.binance_api_secret:
            raise RuntimeError("BINANCE_API_KEY / BINANCE_API_SECRET must be set.")

        self._client = ccxt.binance(
            {
                "apiKey": settings.binance_api_key,
                "secret": settings.binance_api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )
        if settings.binance_testnet:
            self._client.set_sandbox_mode(True)
            logger.info("Binance client initialized in TESTNET (sandbox) mode.")
        else:
            logger.warning("Binance client initialized in MAINNET mode. Real funds at risk.")

        self._markets_loaded = False

    async def _run(self, fn, *args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)

    async def load_markets(self):
        if not self._markets_loaded:
            await self._call_with_retry(self._client.load_markets)
            self._markets_loaded = True

    async def _call_with_retry(self, fn, *args, **kwargs):
        @_retry_decorator()
        async def _inner():
            return await self._run(fn, *args, **kwargs)

        return await _inner()

    # ---------------- Market data ----------------

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int):
        return await self._call_with_retry(self._client.fetch_ohlcv, symbol, timeframe, limit=limit)

    async def fetch_ticker(self, symbol: str):
        return await self._call_with_retry(self._client.fetch_ticker, symbol)

    async def fetch_order_book(self, symbol: str, limit: int = 20):
        return await self._call_with_retry(self._client.fetch_order_book, symbol, limit)

    async def fetch_balance(self):
        return await self._call_with_retry(self._client.fetch_balance)

    async def market_precision(self, symbol: str):
        await self.load_markets()
        market = self._client.market(symbol)
        return market

    def amount_to_precision(self, symbol: str, amount: float) -> float:
        return float(self._client.amount_to_precision(symbol, amount))

    def price_to_precision(self, symbol: str, price: float) -> float:
        return float(self._client.price_to_precision(symbol, price))

    # ---------------- Trading ----------------

    async def create_market_order(self, symbol: str, side: str, amount: float):
        """side: 'buy' or 'sell'. Raises OrderRejected on non-transient failure."""
        try:
            return await self._call_with_retry(
                self._client.create_order, symbol, "market", side, amount
            )
        except TRANSIENT_ERRORS:
            raise
        except ccxt.InsufficientFunds as e:
            raise OrderRejected(f"Insufficient funds: {e}") from e
        except ccxt.InvalidOrder as e:
            raise OrderRejected(f"Invalid order: {e}") from e
        except ccxt.BaseError as e:
            raise OrderRejected(f"Order rejected: {e}") from e

    async def create_oco_sell(self, symbol: str, amount: float, take_profit_price: float, stop_price: float, stop_limit_price: float):
        """
        Places an OCO (One-Cancels-Other) sell order — used to attach a
        take-profit and stop-loss to a long position in a single exchange-side
        bracket, so we don't depend on our own process staying alive to
        protect the position.

        IMPORTANT: the order *type* itself must be 'oco' — ccxt/Binance
        dispatch OCO handling off this positional argument, not off a params
        key. An earlier version of this method passed type='limit' with
        {'type': 'OCO'} buried in params, which Binance would reject (or
        worse, silently execute as an unprotected plain limit sell). Do not
        regress this.
        """
        try:
            return await self._call_with_retry(
                self._client.create_order,
                symbol,
                "oco",
                "sell",
                amount,
                take_profit_price,
                {
                    "stopPrice": stop_price,
                    "stopLimitPrice": stop_limit_price,
                    "stopLimitTimeInForce": "GTC",
                },
            )
        except TRANSIENT_ERRORS:
            raise
        except ccxt.BaseError as e:
            raise OrderRejected(f"OCO bracket rejected: {e}") from e

    async def create_stop_loss_only(self, symbol: str, amount: float, stop_price: float, stop_limit_price: float):
        """
        Fallback protection when the OCO bracket itself is rejected (some
        accounts/symbols don't support OCO, or a transient issue hits only
        that call). This places a plain STOP_LOSS_LIMIT sell — no take-profit
        leg, but it guarantees the exchange, not our process, enforces the
        downside cut. Better than an unprotected position.
        """
        try:
            return await self._call_with_retry(
                self._client.create_order,
                symbol,
                "STOP_LOSS_LIMIT",
                "sell",
                amount,
                stop_limit_price,
                {"stopPrice": stop_price, "timeInForce": "GTC"},
            )
        except TRANSIENT_ERRORS:
            raise
        except ccxt.BaseError as e:
            raise OrderRejected(f"Fallback stop-loss rejected: {e}") from e

    async def create_limit_ioc_order(self, symbol: str, side: str, amount: float, price: float):
        """
        A 'marketable limit' order: priced to fill immediately like a market
        order, but with a hard ceiling/floor on execution price so a thin
        order book can't slip us far worse than expected. If it can't fill
        immediately at an acceptable price, it cancels rather than chasing —
        that's the point.
        """
        try:
            return await self._call_with_retry(
                self._client.create_order,
                symbol, "limit", side, amount, price,
                {"timeInForce": "IOC"},
            )
        except TRANSIENT_ERRORS:
            raise
        except ccxt.InsufficientFunds as e:
            raise OrderRejected(f"Insufficient funds: {e}") from e
        except ccxt.InvalidOrder as e:
            raise OrderRejected(f"Invalid order: {e}") from e
        except ccxt.BaseError as e:
            raise OrderRejected(f"Order rejected: {e}") from e

    async def fetch_my_trades(self, symbol: str, since: int = None, limit: int = 50):
        return await self._call_with_retry(self._client.fetch_my_trades, symbol, since, limit)

    async def cancel_order(self, order_id: str, symbol: str):
        return await self._call_with_retry(self._client.cancel_order, order_id, symbol)

    async def fetch_open_orders(self, symbol: str = None):
        return await self._call_with_retry(self._client.fetch_open_orders, symbol)
