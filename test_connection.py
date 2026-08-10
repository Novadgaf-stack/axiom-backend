"""
Run this before starting the engine to independently verify both external
dependencies are reachable and credentialed correctly:

    python test_connection.py

It does NOT place any orders. It only calls read-only endpoints.
"""
import asyncio
from app.config import settings
from app.exchange import BinanceExchange
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
    print(f"  Testnet mode: {settings.binance_testnet}")
    print(f"  Dry run: {settings.dry_run}")
    print(f"  Trading enabled: {settings.trading_enabled}")

    print("\n" + "=" * 50)
    print("Binance connectivity (read-only)")
    print("=" * 50)
    try:
        ex = BinanceExchange()
        await ex.load_markets()
        ticker = await ex.fetch_ticker(settings.trading_pairs[0])
        print(f"  ✅ Connected. {settings.trading_pairs[0]} last price: {ticker['last']}")
        balance = await ex.fetch_balance()
        usdt = balance.get("total", {}).get("USDT", 0.0)
        print(f"  ✅ Balance fetch OK. USDT total: {usdt}")
    except Exception as e:
        print(f"  ❌ Binance check failed: {e}")

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
