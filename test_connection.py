"""
Run this before starting the engine to independently verify both external
dependencies are reachable and credentialed correctly:

    python test_connection.py

It does NOT place any orders. It only calls read-only endpoints.
"""
import asyncio
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.config import settings
from app.exchange import DataExchange, ExecutionExchange
from app.ai_analyst import AIAnalyst


async def main():
    print("=" * 50)
    print("Config check")
    print("=" * 50)
    problems = settings.validate()
    if problems:
        for p in problems:
            print(f"  ⚠️  {p}")
    else:
        print("  All required settings present.")
    print(f"  Data Exchange: {settings.data_exchange_id}")
    print(f"  Execution Exchange: {settings.execution_exchange_id}")
    print(f"  Testnet mode: {settings.binance_testnet}")
    print(f"  Dry run: {settings.dry_run}")
    print(f"  Trading enabled: {settings.trading_enabled}")
    if settings.http_proxy or settings.https_proxy:
        print(f"  HTTP Proxy: {settings.http_proxy}")
        print(f"  HTTPS Proxy: {settings.https_proxy}")

    print("\n" + "=" * 50)
    print(f"Data Exchange connectivity ({settings.data_exchange_id})")
    print("=" * 50)
    try:
        data_ex = DataExchange()
        await data_ex.load_markets()
        ticker = await data_ex.fetch_ticker(settings.trading_pairs[0])
        print(f"  ✅ Data exchange connected. {settings.trading_pairs[0]} last price: {ticker['last']}")
    except Exception as e:
        print(f"  ❌ Data exchange check failed: {e}")

    print("\n" + "=" * 50)
    print(f"Execution Exchange connectivity ({settings.execution_exchange_id})")
    print("=" * 50)
    try:
        exec_ex = ExecutionExchange()
        await exec_ex.load_markets()
        balance = await exec_ex.fetch_balance()
        usdt = balance.get("total", {}).get("USDT", 0.0)
        print(f"  ✅ Execution exchange connected. Balance fetch OK. USDT total: {usdt}")
    except Exception as e:
        err_str = str(e)
        if "451" in err_str:
            print(f"  ⚠️  Execution exchange geoblocked (HTTP 451). Supply HTTP_PROXY or switch EXECUTION_EXCHANGE_ID.")
        else:
            print(f"  ❌ Execution exchange check failed: {e}")

    print("\n" + "=" * 50)
    print("Gemini connectivity")
    print("=" * 50)
    try:
        analyst = AIAnalyst()
        result = await analyst.analyze(
            symbol="BTC/USDT",
            technical={"close": 65000, "rsi_14": 55, "technical_bias": "LONG"},
            order_book_summary={"order_book_imbalance": 0.1},
        )
        if result.is_valid:
            print(f"  ✅ Gemini responded validly: {result.decision}")
        else:
            print(f"  ❌ Gemini response failed validation: {result.error}")
    except Exception as e:
        print(f"  ❌ Gemini check failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
