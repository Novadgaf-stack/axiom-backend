#!/usr/bin/env python3
"""
Backtest harness for the Nexus-7 engine's technical + AI-gated strategy.

Reuses the exact production modules under test (app.indicators,
app.risk.RiskManager, app.strategy.StrategyEngine) so results reflect what
the live engine actually does — not a reimplementation that could drift.

USAGE
-----
Quick smoke test with synthetic data (no network, no API keys, ~seconds):
    python backtest.py --source synthetic --days 180 --mode technical_only

Real historical data, comparing technical-only vs AI-filtered:
    python backtest.py --source binance --symbol BTC/USDT --timeframe 15m \\
        --days 365 --compare

Live Gemini calls (slow, costs money — capped and rate-limited):
    export GEMINI_API_KEY=...
    python backtest.py --source binance --days 14 --mode ai_live --max-live-calls 300

See `python backtest.py --help` for all options.
"""
import argparse
import asyncio
import csv
import dataclasses
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Settings
from backtest.data_source import fetch_binance_history, load_csv_history, generate_synthetic_history
from backtest.mock_ai_analyst import MockAiAnalyst
from backtest.simulator import BacktestSimulator
from backtest.metrics import compute_report


def build_settings(args) -> Settings:
    base = Settings()
    overrides = {}
    for cli_name, field_name in [
        ("min_confidence", "min_confidence_score"),
        ("atr_sl", "atr_sl_multiplier"),
        ("atr_tp", "atr_tp_multiplier"),
        ("atr_period", "atr_period"),
        ("min_volume_ratio", "min_volume_ratio"),
        ("cooldown_minutes", "cooldown_minutes_after_loss"),
        ("max_daily_loss_pct", "max_daily_loss_pct"),
        ("risk_per_trade_pct", "risk_per_trade_pct"),
        ("max_position_pct", "max_position_pct"),
        ("min_trade_notional", "min_trade_notional_usd"),
    ]:
        val = getattr(args, cli_name, None)
        if val is not None:
            overrides[field_name] = val
    if args.no_technical_confirmation:
        overrides["require_technical_confirmation"] = False
    return dataclasses.replace(base, **overrides) if overrides else base


def apply_settings_override(settings_obj: Settings):
    """
    app.risk and app.strategy do `from app.config import settings` — that
    binds a name in each module's namespace, but function bodies resolve
    that name from the module's globals AT CALL TIME, so reassigning the
    module attribute here (before running any trades) correctly redirects
    every settings.* lookup those modules make, without touching the
    production files or requiring a .env file to exist.
    """
    import app.risk as risk_mod
    import app.strategy as strategy_mod
    risk_mod.settings = settings_obj
    strategy_mod.settings = settings_obj


def load_candles(args) -> list:
    if args.source == "synthetic":
        print("NOTE: synthetic data is for exercising the harness mechanics only — "
              "it has no relationship to real markets. Do not draw edge conclusions from it.")
        tf_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}.get(args.timeframe, 15)
        return generate_synthetic_history(days=args.days, timeframe_minutes=tf_minutes, seed=args.seed)
    elif args.source == "csv":
        if not args.csv_path:
            sys.exit("--csv-path is required when --source csv")
        return load_csv_history(args.csv_path)
    else:
        return fetch_binance_history(
            symbol=args.symbol, timeframe=args.timeframe, days=args.days,
            cache_dir=args.cache_dir, refresh=args.no_cache,
        )


def build_analyst(mode: str, args):
    if mode == "ai_live":
        from app.ai_analyst import AIAnalyst
        if not os.getenv("GEMINI_API_KEY"):
            sys.exit("--mode ai_live requires GEMINI_API_KEY to be set.")
        real = AIAnalyst()
        return RateLimitedLiveAnalyst(real, max_calls=args.max_live_calls, delay_seconds=args.live_call_delay)
    return MockAiAnalyst(mode=mode, seed=args.seed)


class RateLimitedLiveAnalyst:
    """Wraps the real AIAnalyst with a hard call cap and a fixed delay
    between calls — a naive backtest loop calling a live LLM API thousands
    of times will be slow, expensive, and likely rate-limited without this."""
    def __init__(self, real_analyst, max_calls: int, delay_seconds: float):
        self.real = real_analyst
        self.max_calls = max_calls
        self.delay_seconds = delay_seconds
        self.call_count = 0

    async def analyze(self, symbol, technical, order_book_summary):
        if self.call_count >= self.max_calls:
            from app.ai_analyst import AnalystResult
            return AnalystResult(decision=None, raw_text="", error="max_live_calls_cap_reached")
        self.call_count += 1
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        return await self.real.analyze(symbol, technical, order_book_summary)


async def run_one(mode: str, candles: list, args, settings_obj: Settings):
    analyst = build_analyst(mode, args)
    sim = BacktestSimulator(
        candles=candles,
        symbol=args.symbol,
        analyst=analyst,
        settings_obj=settings_obj,
        initial_equity=args.initial_equity,
        fee_pct=args.fee_pct,
        slippage_pct=args.slippage_pct,
        max_hold_bars=args.max_hold_bars,
        same_bar_conflict=args.same_bar_conflict,
    )
    trades = await sim.run()
    call_count = getattr(analyst, "call_count", 0)
    report = compute_report(
        trades=trades, initial_equity=args.initial_equity, mode=mode,
        symbol=args.symbol, timeframe=args.timeframe, total_candles=len(candles),
        ai_calls_made=call_count,
    )
    return report


def save_outputs(report, out_dir: str, mode: str):
    os.makedirs(out_dir, exist_ok=True)
    trades_path = os.path.join(out_dir, f"trades_{mode}.csv")
    equity_path = os.path.join(out_dir, f"equity_curve_{mode}.csv")
    report_path = os.path.join(out_dir, f"report_{mode}.json")

    with open(trades_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "entry_time_ms", "exit_time_ms", "entry_price", "exit_price", "quantity",
            "stop_loss", "take_profit", "exit_reason", "pnl_usd", "r_multiple", "fees_usd",
        ])
        for t in report.trades:
            writer.writerow([
                t.entry_time_ms, t.exit_time_ms, t.entry_price, t.exit_price, t.quantity,
                t.stop_loss, t.take_profit, t.exit_reason, round(t.pnl_usd, 4),
                round(t.r_multiple, 3), round(t.fees_usd, 4),
            ])

    with open(equity_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "equity_usd"])
        writer.writerows(report.equity_curve)

    summary = {k: v for k, v in dataclasses.asdict(report).items() if k not in ("trades", "equity_curve")}
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved: {trades_path}, {equity_path}, {report_path}")


def print_comparison(reports: dict):
    cols = ["mode", "trades", "win_rate%", "profit_factor", "expectancy($)", "expectancy(R)", "max_dd%", "net_pnl%"]
    print("\n" + "=" * 90)
    print("COMPARATIVE SUMMARY")
    print("=" * 90)
    header = "{:<16}{:>9}{:>11}{:>15}{:>15}{:>15}{:>10}{:>12}".format(*cols)
    print(header)
    for mode, r in reports.items():
        print("{:<16}{:>9}{:>11.2f}{:>15.2f}{:>15.2f}{:>15.2f}{:>10.2f}{:>12.2f}".format(
            mode, r.total_trades, r.win_rate_pct, r.profit_factor,
            r.expectancy_usd, r.expectancy_r, r.max_drawdown_pct, r.net_pnl_pct,
        ))
    print("=" * 90)
    print(
        "Read this comparison as: does adding the AI confidence gate (ai_mirror) actually\n"
        "improve on trading every technical signal (technical_only)? If ai_mirror doesn't\n"
        "beat technical_only by a meaningful margin — and beat ai_random by more than\n"
        "ai_mirror beats technical_only — that's evidence the AI layer isn't adding real\n"
        "filtering value, only extra latency and API cost. Remember: 'ai_mirror' is a\n"
        "heuristic stand-in, not a real Gemini forecast — this compares FILTERING BEHAVIOR,\n"
        "not Gemini's actual predictive power, which can only be validated with ai_live\n"
        "or, better, forward paper-trading."
    )


def main():
    parser = argparse.ArgumentParser(description="Backtest the Nexus-7 technical + AI-gated strategy.")
    parser.add_argument("--source", choices=["binance", "synthetic", "csv"], default="binance")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--csv-path", default=None)
    parser.add_argument("--cache-dir", default="./data/historical")
    parser.add_argument("--no-cache", action="store_true", help="Force refetch even if a cached CSV exists.")

    parser.add_argument("--mode", choices=["technical_only", "ai_mirror", "ai_random", "ai_live"], default="ai_mirror")
    parser.add_argument("--compare", action="store_true", help="Run technical_only + ai_mirror + ai_random and print a side-by-side comparison.")

    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    parser.add_argument("--fee-pct", type=float, default=0.1, help="Per-side fee, e.g. 0.1 for Binance spot taker.")
    parser.add_argument("--slippage-pct", type=float, default=0.05)
    parser.add_argument("--max-hold-bars", type=int, default=96, help="Force-close a trade after this many bars if neither SL nor TP is hit.")
    parser.add_argument("--same-bar-conflict", choices=["conservative", "optimistic"], default="conservative",
                         help="When a single bar's range touches both SL and TP, which is assumed hit first. 'conservative' (SL first) avoids flattering the backtest.")

    parser.add_argument("--min-confidence", type=int, default=None)
    parser.add_argument("--atr-sl", type=float, default=None)
    parser.add_argument("--atr-tp", type=float, default=None)
    parser.add_argument("--atr-period", type=int, default=None)
    parser.add_argument("--min-volume-ratio", type=float, default=None)
    parser.add_argument("--cooldown-minutes", type=int, default=None)
    parser.add_argument("--max-daily-loss-pct", type=float, default=None)
    parser.add_argument("--risk-per-trade-pct", type=float, default=None)
    parser.add_argument("--max-position-pct", type=float, default=None)
    parser.add_argument("--min-trade-notional", type=float, default=None)
    parser.add_argument("--no-technical-confirmation", action="store_true",
                         help="Disable requiring AI direction to agree with technical bias (for experimentation only).")

    parser.add_argument("--max-live-calls", type=int, default=200, help="Hard cap on real Gemini API calls in ai_live mode.")
    parser.add_argument("--live-call-delay", type=float, default=1.0, help="Seconds to sleep between ai_live calls.")

    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="./backtest_results")

    args = parser.parse_args()

    settings_obj = build_settings(args)
    apply_settings_override(settings_obj)

    t0 = time.time()
    candles = load_candles(args)
    print(f"Loaded {len(candles)} candles in {time.time()-t0:.1f}s.")
    if len(candles) < 200:
        print("WARNING: fewer than 200 candles — results will not be statistically meaningful.")

    modes_to_run = ["technical_only", "ai_mirror", "ai_random"] if args.compare else [args.mode]

    reports = {}
    for mode in modes_to_run:
        print(f"\nRunning backtest: mode={mode} ...")
        t0 = time.time()
        report = asyncio.run(run_one(mode, candles, args, settings_obj))
        print(f"  done in {time.time()-t0:.1f}s")
        report.print_summary()
        save_outputs(report, args.out_dir, mode)
        reports[mode] = report

    if len(reports) > 1:
        print_comparison(reports)


if __name__ == "__main__":
    main()
