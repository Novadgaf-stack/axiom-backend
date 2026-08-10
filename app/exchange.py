"""
Decoupled exchange wrappers built on ccxt.

Architecture:
- DataExchange: Handles unauthenticated public market data (OHLCV, indicators, orderbook).
  Configurable via DATA_EXCHANGE_ID (default: "bybit").
- ExecutionExchange: Handles authenticated account operations (orders, balances, trade history).
  Configurable via EXECUTION_EXCHANGE_ID (default: "binance"). Supports HTTP/HTTPS proxies.

Design notes:
- All network calls run through `tenacity` retry with exponential backoff for transient errors.
- Synchronous ccxt calls are offloaded to a thread via asyncio.to_thread.
- Graceful error handling for HTTP 451 / ExchangeNotAvailable during startup load_markets().
"""
import asyncio
import logging
from typing import Optional, Dict
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


def _build_proxies_dict() -> Optional[Dict[str, str]]:
    proxies = {}
    if settings.http_proxy:
        proxies["http"] = settings.http_proxy
    if settings.https_proxy:
        proxies["https"] = settings.https_proxy
    return proxies if proxies else None


class BaseExchangeWrapper:
    def __init__(self, exchange_id: str, config: dict):
        self.exchange_id = exchange_id.lower()
        if not hasattr(ccxt, self.exchange_id):
            raise ValueError(f"Exchange '{self.exchange_id}' is not supported by ccxt.")

        proxies = _build_proxies_dict()
        if proxies:
            config["proxies"] = proxies
            logger.info(f"[{self.exchange_id}] Configured HTTP/HTTPS proxies.")

        exchange_cls = getattr(ccxt, self.exchange_id)
        self._client = exchange_cls(config)
        self._markets_loaded = False

    async def _run(self, fn, *args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)

    async def _call_with_retry(self, fn, *args, **kwargs):
        @_retry_decorator()
        async def _inner():
            return await self._run(fn, *args, **kwargs)

        return await _inner()

    async def load_markets(self):
        if not self._markets_loaded:
            try:
                await self._call_with_retry(self._client.load_markets)
                self._markets_loaded = True
                logger.info(f"[{self.exchange_id}] Markets loaded successfully.")
            except Exception as e:
                err_str = str(e)
                if "451" in err_str or isinstance(e, ccxt.ExchangeNotAvailable):
                    if not settings.http_proxy and not settings.https_proxy:
                        logger.warning(
                            "Execution exchange geoblocked (HTTP 451). Supply HTTP_PROXY or switch EXECUTION_EXCHANGE_ID."
                        )
                    else:
                        logger.warning(
                            f"[{self.exchange_id}] Failed to load markets due to ExchangeNotAvailable/451: {e}"
                        )
                else:
                    logger.warning(f"[{self.exchange_id}] Failed to load markets: {e}")

    async def market_precision(self, symbol: str):
        await self.load_markets()
        try:
            return self._client.market(symbol)
        except Exception as e:
            logger.warning(f"[{self.exchange_id}] Could not fetch market precision for {symbol}: {e}")
            return {}

    def amount_to_precision(self, symbol: str, amount: float) -> float:
        try:
            return float(self._client.amount_to_precision(symbol, amount))
        except Exception:
            return amount

    def price_to_precision(self, symbol: str, price: float) -> float:
        try:
            return float(self._client.price_to_precision(symbol, price))
        except Exception:
            return price


class DataExchange(BaseExchangeWrapper):
    """Exchange instance dedicated to public market data (OHLCV, orderbook, tickers)."""

    def __init__(self, exchange_id: str = None):
        eid = exchange_id or settings.data_exchange_id
        config = {
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
        super().__init__(eid, config)
        logger.info(f"DataExchange initialized for '{self.exchange_id}'.")

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int):
        return await self._call_with_retry(self._client.fetch_ohlcv, symbol, timeframe, limit=limit)

    async def fetch_ticker(self, symbol: str):
        return await self._call_with_retry(self._client.fetch_ticker, symbol)

    async def fetch_order_book(self, symbol: str, limit: int = 20):
        return await self._call_with_retry(self._client.fetch_order_book, symbol, limit)


class ExecutionExchange(BaseExchangeWrapper):
    """Exchange instance dedicated to authenticated operations (orders, balances, trade history)."""

    def __init__(self, exchange_id: str = None, api_key: str = None, api_secret: str = None):
        eid = exchange_id or settings.execution_exchange_id
        key = api_key or settings.binance_api_key
        secret = api_secret or settings.binance_api_secret

        config = {
            "apiKey": key,
            "secret": secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
        super().__init__(eid, config)

        if self.exchange_id == "binance" and settings.binance_testnet:
            if hasattr(self._client, "set_sandbox_mode"):
                try:
                    self._client.set_sandbox_mode(True)
                    logger.info("Binance execution client initialized in TESTNET (sandbox) mode.")
                except Exception as e:
                    logger.warning(f"Could not set sandbox mode: {e}")
        else:
            logger.warning(f"Execution exchange '{self.exchange_id}' initialized in MAINNET mode. Real funds at risk.")

    async def fetch_balance(self):
        return await self._call_with_retry(self._client.fetch_balance)

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


# Backward-compatibility alias
BinanceExchange = ExecutionExchange
