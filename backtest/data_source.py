"""
Historical OHLCV ingestion for the backtester.

Two sources:
  - binance:   real historical candles via ccxt, paginated, cached to CSV.
               Uses PUBLIC market-data endpoints only (no API key needed,
               and deliberately NOT pointed at testnet — testnet has thin,
               short, sometimes synthetic history; real edge testing needs
               real historical mainnet data. This module never places
               orders, so there's no live-trading-safety implication to
               pulling from mainnet market data here.)
  - synthetic: a regime-switching random walk, generated locally, no
               network required. This exists ONLY to smoke-test that the
               backtest mechanics (no look-ahead, SL/TP detection, metrics
               math) work correctly. It has no relationship to real market
               behavior — never draw conclusions about strategy edge from
               synthetic-mode results.
  - csv:       load a pre-existing CSV you already have.
"""
import csv
import os
import random
import time

CSV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def _cache_path(cache_dir: str, symbol: str, timeframe: str, start_ms: int, end_ms: int) -> str:
    safe_symbol = symbol.replace("/", "")
    return os.path.join(cache_dir, f"{safe_symbol}_{timeframe}_{start_ms}_{end_ms}.csv")


def _read_csv(path: str) -> list:
    candles = []
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            candles.append([int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])])
    return candles


def _write_csv(path: str, candles: list):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(candles)


def fetch_binance_history(symbol: str, timeframe: str, days: int, cache_dir: str, refresh: bool = False, verbose: bool = True) -> list:
    import ccxt

    now_ms = int(time.time() * 1000)
    start_ms = now_ms - days * 24 * 60 * 60 * 1000
    path = _cache_path(cache_dir, symbol, timeframe, start_ms // 3600000 * 3600000, now_ms // 3600000 * 3600000)

    if not refresh and os.path.exists(path):
        if verbose:
            print(f"Loading cached history: {path}")
        return _read_csv(path)

    exchanges_to_try = ["binance", "bybit", "kraken"]
    all_candles = []

    for ex_id in exchanges_to_try:
        if not hasattr(ccxt, ex_id):
            continue
        try:
            exchange_cls = getattr(ccxt, ex_id)
            exchange = exchange_cls({"enableRateLimit": True, "timeout": 15000})
            timeframe_ms = exchange.parse_timeframe(timeframe) * 1000
            since = start_ms
            limit = 1000

            if verbose:
                print(f"Fetching {symbol} {timeframe} from {ex_id}, last {days} days...")

            candles_batch = []
            while since < now_ms:
                batch = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                if not batch:
                    break
                candles_batch.extend(batch)
                last_ts = batch[-1][0]
                if last_ts <= since:
                    break
                since = last_ts + timeframe_ms
                if len(batch) < limit:
                    break
                time.sleep(exchange.rateLimit / 1000)

            if candles_batch:
                all_candles = candles_batch
                if verbose:
                    print(f"Successfully fetched {len(all_candles)} candles from {ex_id}.")
                break
        except Exception as e:
            if verbose:
                print(f"Fetch from {ex_id} failed ({e}), trying next exchange...")
            continue

    if not all_candles:
        raise RuntimeError("Failed to fetch historical candles from all public exchanges (binance, bybit, kraken).")

    all_candles = [c for c in all_candles if c[0] <= now_ms]
    dedup = {c[0]: c for c in all_candles}
    all_candles = sorted(dedup.values(), key=lambda c: c[0])

    _write_csv(path, all_candles)
    if verbose:
        print(f"Fetched {len(all_candles)} candles. Cached to {path}")
    return all_candles



def load_csv_history(path: str) -> list:
    return _read_csv(path)


def generate_synthetic_history(days: int, timeframe_minutes: int = 15, start_price: float = 50000.0, seed: int = 7) -> list:
    """
    Regime-switching synthetic OHLCV: alternates trending and choppy/ranging
    segments so the harness has non-trivial structure to react to. This is
    for testing the BACKTEST MECHANICS ONLY. It is not a market simulator
    and proves nothing about real strategy performance.
    """
    rng = random.Random(seed)
    bars_per_day = int(24 * 60 / timeframe_minutes)
    n = days * bars_per_day
    candles = []
    price = start_price
    ts = int(time.time() * 1000) - n * timeframe_minutes * 60 * 1000

    regime_len = rng.randint(bars_per_day * 2, bars_per_day * 8)
    regime_drift = rng.uniform(-0.0006, 0.0008)
    bars_in_regime = 0

    for i in range(n):
        if bars_in_regime >= regime_len:
            regime_len = rng.randint(bars_per_day * 2, bars_per_day * 8)
            regime_drift = rng.uniform(-0.0006, 0.0008)
            bars_in_regime = 0

        noise = rng.gauss(0, 0.0025)
        change = regime_drift + noise
        o = price
        price = max(price * (1 + change), 1.0)
        c = price
        wick = abs(rng.gauss(0, 0.0015)) * price
        h = max(o, c) + wick
        l = max(min(o, c) - wick, 0.01)
        base_vol = 50 + 40 * abs(noise) * 100
        v = max(base_vol * rng.uniform(0.4, 1.8), 1.0)

        candles.append([ts + i * timeframe_minutes * 60 * 1000, round(o, 4), round(h, 4), round(l, 4), round(c, 4), round(v, 4)])
        bars_in_regime += 1

    return candles
