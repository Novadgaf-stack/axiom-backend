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
        ("t1_tp", "t1_tp_multiplier"),
        ("t2_tp", "t2_tp_multiplier"),
        ("atr_period", "atr_period"),
        ("min_volume_ratio", "min_volume_ratio"),
        ("min_adx", "min_adx"),
        ("cooldown_minutes", "cooldown_minutes_after_loss"),
        ("max_daily_loss_pct", "max_daily_loss_pct"),
        ("risk_per_trade_pct", "risk_per_trade_pct"),
        ("max_position_pct", "max_position_pct"),
        ("min_trade_notional", "min_trade_notional_usd"),
    ]:
        val = getattr(args, cli_name, None)
        if val is not None:
            overrides[field_name] = val
    if getattr(args, "no_technical_confirmation", False):
        overrides["require_technical_confirmation"] = False
    if getattr(args, "enable_session_filter", False):
        overrides["enable_session_filter"] = True
    if getattr(args, "disable_confidence_scaling", False):
        overrides["confidence_scaling_enabled"] = False
    if getattr(args, "disable_multi_stage_exits", False):
        overrides["enable_multi_stage_exits"] = False

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
    import logging
    import app.risk as risk_mod
    import app.strategy as strategy_mod
    risk_mod.settings = settings_obj
    strategy_mod.settings = settings_obj
    risk_mod.logger.setLevel(logging.ERROR)
    strategy_mod.logger.setLevel(logging.ERROR)


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
    cols = ["mode", "trades (W/L)", "win_rate%", "profit_factor", "sharpe", "expectancy($)", "expectancy(R)", "max_dd%", "net_pnl%"]
    print("\n" + "=" * 110)
    print("INSTITUTIONAL COMPARATIVE SUMMARY")
    print("=" * 110)
    header = "{:<16}{:>14}{:>11}{:>15}{:>10}{:>15}{:>15}{:>10}{:>12}".format(*cols)
    print(header)
    for mode, r in reports.items():
        trade_str = f"{r.total_trades} ({r.winning_trades}W/{r.losing_trades}L)"
        print("{:<16}{:>14}{:>11.2f}{:>15.2f}{:>10.2f}{:>15.2f}{:>15.2f}{:>10.2f}{:>12.2f}".format(
            mode, trade_str, r.win_rate_pct, r.profit_factor, r.sharpe_ratio,
            r.expectancy_usd, r.expectancy_r, r.max_drawdown_pct, r.net_pnl_pct,
        ))
    print("=" * 110)
    print(
        "ROBUSTNESS DISCIPLINE REMINDER:\n"
        "• Evaluate sample size (W/L trades count) — single-digit trade counts have high sampling error.\n"
        "• Compare ai_mirror (heuristic AI filter) against technical_only (baseline) and ai_random (null control).\n"
        "• Always validate parameter choices with an Out-of-Sample (OOS) locked walk-forward period."
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
    parser.add_argument("--validate", action="store_true", help="Run full institutional validation suite (IS/OOS, Walk-Forward, Regimes, Sensitivity, AI Edge, Monte Carlo) and generate NEXUS-7 STRATEGY VALIDATION REPORT.")
    parser.add_argument("--run-v2-experiments", action="store_true", help="Run NEXUS-7 Pullback v2 controlled incremental experiment series (Experiments A through E) on frozen dataset.")
    parser.add_argument("--run-candidates", action="store_true", help="Run candidate evaluation matrix (Candidate A: 15m pullback, Candidate B: 1h pullback, Candidate C: 1h V2 Candidate D).")
    parser.add_argument("--run-sensitivity-matrix", action="store_true", help="Run execution friction sensitivity matrix for Candidate C (Optimistic/Normal/Conservative Maker vs Taker).")
    parser.add_argument("--run-frozen-oos", action="store_true", help="Run frozen temporal Out-of-Sample (OOS) holdout evaluation for Candidate C without modifying parameters.")
    parser.add_argument("--run-regime-research", action="store_true", help="Extract multidimensional trade regime feature dataset and run Gemini 2.0 Flash AI regime analysis.")
    parser.add_argument("--run-diversity-expansion", action="store_true", help="Run cross-asset and sample diversity expansion for Benchmark v1 (BTC/USDT, ETH/USDT 365-day datasets).")
    parser.add_argument("--run-robustness-audit", action="store_true", help="Run statistical significance & robustness audit (10,000 bootstrap iterations, quarterly consistency, multi-asset friction matrix).")
    parser.add_argument("--run-edge-decomposition", action="store_true", help="Run edge decomposition & realism study (trade attribution, outlier concentration, random baseline control, fill realism).")
    parser.add_argument("--run-strategy-tournament", action="store_true", help="Run strategy-vs-controls tournament (Benchmark v1 vs 6 non-AI / simple technical controls under 0.04%% maker fee).")
    parser.add_argument("--run-strategy-research", action="store_true", help="Run multi-asset, multi-family strategy research suite (EXP-001 through EXP-006, PBO, walk-forward, controls, and 11 deliverables).")
    parser.add_argument("--run-research-v2", action="store_true", help="Run Research Reset V2 laboratory (Phase 0 engine audit, Phase 1-12 multi-asset candidate suite, and 14 deliverables).")
    parser.add_argument("--run-research-v3", action="store_true", help="Run Research V3 Alpha Discovery framework (7 independent hypotheses, 3-tier cost stress, multi-window walk-forward, and 11 deliverables).")
    parser.add_argument("--run-research-v4", action="store_true", help="Run Research V4 Competition-Grade Strategy Engine (Multi-hypothesis ensemble, regime classifier, walk-forward, PBO, Buy-and-Hold benchmark).")
    parser.add_argument("--run-research-v5", action="store_true", help="Run Research V5 Alpha Selection & Verification Framework (Triple-barrier labeling, MTF, Binance microstructure, Purged CV, Ablation, DSR, 7-stage promotion gate).")
    parser.add_argument("--run-research-v6", action="store_true", help="Run Research V6 Structural Alpha Discovery Engine (4 non-ML structural hypotheses evaluated against V5 Promotion Gate).")
    parser.add_argument("--run-research-v7", action="store_true", help="Run Research V7 MTF-TP Deep Robustness & Attribution Audit (10-step robustness, parameter perturbation grid, asset separation, cost stress).")
    parser.add_argument("--run-research-v8", action="store_true", help="Run Research V8 Microstructure & Portfolio Alpha Engine (Volume Delta, CVD, BTC/ETH pair spread reversion evaluated against V5 Promotion Gate).")
    parser.add_argument("--run-research-v9", action="store_true", help="Run Research V9 Microstructure Data Quality & Live Execution Parity Audit (10-point audit across data quality, engine parity, and portfolio risk integration).")
    parser.add_argument("--run-research-v10", action="store_true", help="Run Research V10 Real Market Data & Portfolio Drawdown Guard Engine (Real CCXT trade ticks, L2 order book depth, and hard 15%% drawdown circuit breaker).")
    parser.add_argument("--run-research-v11", action="store_true", help="Run Research V11 Order Book Feature Transformer & Leakage Auditor Engine (Mathematical order book features and zero data leakage audit).")







    parser.add_argument("--run-testnet-certification", action="store_true", help="Run Testnet Operations & Chaos Certification evaluator (Phases 1-4, failure injections, and testnet_certification_report.md).")


    parser.add_argument("--run-testnet-soak", action="store_true", help="Run 24h Real Testnet Operational Validation & Soak certifier (Phases 1-12, all 6 artifacts).")
    parser.add_argument("--soak-hours", type=float, default=24.0, help="Target soak hours for operational validation report (default 24.0).")

    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    parser.add_argument("--fee-pct", type=float, default=0.1, help="Per-side fee, e.g. 0.1 for Binance spot taker.")
    parser.add_argument("--slippage-pct", type=float, default=0.05)
    parser.add_argument("--max-hold-bars", type=int, default=96, help="Force-close a trade after this many bars if neither SL nor TP is hit.")
    parser.add_argument("--same-bar-conflict", choices=["conservative", "optimistic"], default="conservative",
                         help="When a single bar's range touches both SL and TP, which is assumed hit first. 'conservative' (SL first) avoids flattering the backtest.")

    parser.add_argument("--min-confidence", type=int, default=None)
    parser.add_argument("--atr-sl", type=float, default=None)
    parser.add_argument("--atr-tp", type=float, default=None)
    parser.add_argument("--t1-tp", type=float, default=None, help="ATR multiplier for Tranche 1 scale-out (default 1.0)")
    parser.add_argument("--t2-tp", type=float, default=None, help="ATR multiplier for Tranche 2 final target (default 2.5)")
    parser.add_argument("--atr-period", type=int, default=None)
    parser.add_argument("--min-volume-ratio", type=float, default=None)
    parser.add_argument("--min-adx", type=float, default=None, help="Minimum ADX threshold for trend strength filter (default 20.0)")
    parser.add_argument("--enable-session-filter", action="store_true", help="Restrict trade generation to 12:00-20:00 UTC liquidity window")
    parser.add_argument("--disable-confidence-scaling", action="store_true", help="Disable dynamic confidence-weighted position sizing")
    parser.add_argument("--disable-multi-stage-exits", action="store_true", help="Disable multi-stage exits (use single TP target instead)")
    parser.add_argument("--cooldown-minutes", type=int, default=None)
    parser.add_argument("--max-daily-loss-pct", type=float, default=None)
    parser.add_argument("--risk-per-trade-pct", type=float, default=None)
    parser.add_argument("--max-position-pct", type=float, default=None)
    parser.add_argument("--min-trade-notional", type=float, default=None)
    parser.add_argument("--no-technical-confirmation", action="store_true",
                         help="Disable requiring AI direction to agree with technical bias (for experimentation only).")

    parser.add_argument("--max-live-calls", type=int, default=200, help="Hard cap on real Gemini API calls in ai_live mode.")
    parser.add_argument("--live-call-delay", type=float, default=1.0, help="Seconds to sleep between ai_live calls.")

    parser.add_argument("--trace-trade", type=int, default=None, help="Print detailed diagnostic trace for a specific trade ID (1-indexed).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="./backtest_results")

    args = parser.parse_args()

    settings_obj = build_settings(args)
    apply_settings_override(settings_obj)

    if args.run_diversity_expansion:
        from backtest.validation import run_sample_diversity_expansion
        print("\n" + "=" * 80)
        print("RUNNING CROSS-ASSET & SAMPLE DIVERSITY EXPANSION...")
        print("=" * 80)
        diversity_md = run_sample_diversity_expansion("./data/historical", settings_obj)
        report_path = os.path.join(args.out_dir, "sample_diversity_expansion_report.md")
        os.makedirs(args.out_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(diversity_md)
        print(diversity_md)
        print(f"\nSaved Sample Diversity Expansion Report to: {report_path}")
        return

    if args.run_robustness_audit:
        from backtest.validation import run_statistical_robustness_audit
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 STATISTICAL SIGNIFICANCE & ROBUSTNESS AUDIT...")
        print("=" * 80)
        audit_md = run_statistical_robustness_audit("./data/historical", settings_obj)
        report_path = os.path.join(args.out_dir, "robustness_audit_report.md")
        os.makedirs(args.out_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(audit_md)
        print(audit_md)
        print(f"\nSaved Robustness Audit Report to: {report_path}")
        return

    if args.run_edge_decomposition:
        from backtest.validation import run_edge_decomposition_study
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 EDGE DECOMPOSITION & REALISM STUDY...")
        print("=" * 80)
        decomp_md = run_edge_decomposition_study("./data/historical", settings_obj)
        report_path = os.path.join(args.out_dir, "edge_decomposition_report.md")
        os.makedirs(args.out_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(decomp_md)
        print(decomp_md)
        print(f"\nSaved Edge Decomposition Report to: {report_path}")
        return

    if args.run_strategy_tournament:
        from backtest.validation import run_strategy_tournament_suite
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 STRATEGY-VS-CONTROLS TOURNAMENT...")
        print("=" * 80)
        tourn_md = run_strategy_tournament_suite("./data/historical", settings_obj)
        report_path = os.path.join(args.out_dir, "strategy_tournament_report.md")
        os.makedirs(args.out_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(tourn_md)
        print(tourn_md)
        print(f"\nSaved Strategy Tournament Report to: {report_path}")
        return

    if args.run_strategy_research:
        from backtest.research.pipeline import run_full_strategy_research_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 MULTI-ASSET STRATEGY RESEARCH RESET PIPELINE...")
        print("=" * 80)
        report_md = run_full_strategy_research_pipeline("./data/historical", settings_obj, "./strategy_research")
        print("\n" + report_md.encode('ascii', errors='ignore').decode('ascii'))
        return

    if args.run_research_v2:
        from backtest.research_v2.pipeline import run_full_research_v2_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 QUANT RESEARCH RESET V2 LABORATORY...")
        print("=" * 80)
        report_md = run_full_research_v2_pipeline("./data/historical", settings_obj, "./research_v2")
        print("\n" + report_md.encode('ascii', errors='ignore').decode('ascii'))
        return

    if args.run_research_v3:
        from backtest.research_v3.pipeline import run_full_research_v3_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V3 ALPHA DISCOVERY FRAMEWORK...")
        print("=" * 80)
        res = run_full_research_v3_pipeline("./data/historical", settings_obj, "./research_v3")
        return

    if args.run_research_v4:
        from backtest.research_v4.pipeline import run_full_research_v4_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V4 COMPETITION-GRADE STRATEGY ENGINE...")
        print("=" * 80)
        res = run_full_research_v4_pipeline("./data/historical", "research_v4_report.md")
        return

    if args.run_research_v5:
        from backtest.research_v5.pipeline import run_full_research_v5_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V5 ALPHA SELECTION & VERIFICATION FRAMEWORK...")
        print("=" * 80)
        res = run_full_research_v5_pipeline("./data/historical", "research_v5_report.md")
        return

    if args.run_research_v6:
        from backtest.research_v6.pipeline import run_full_research_v6_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V6 STRUCTURAL ALPHA DISCOVERY ENGINE...")
        print("=" * 80)
        res = run_full_research_v6_pipeline("./data/historical", "research_v6_report.md")
        return

    if args.run_research_v7:
        from backtest.research_v7.pipeline import run_full_research_v7_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V7 MTF-TP DEEP ROBUSTNESS & ATTRIBUTION AUDIT...")
        print("=" * 80)
        res = run_full_research_v7_pipeline("./data/historical", "research_v7_mtf_tp_report.md")
        return

    if args.run_research_v8:
        from backtest.research_v8.pipeline import run_full_research_v8_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V8 MICROSTRUCTURE & PORTFOLIO ALPHA ENGINE...")
        print("=" * 80)
        res = run_full_research_v8_pipeline("./data/historical", "research_v8_report.md")
        return

    if args.run_research_v9:
        from backtest.research_v9.pipeline import run_full_research_v9_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V9 MICROSTRUCTURE DATA QUALITY & LIVE PARITY AUDIT...")
        print("=" * 80)
        res = run_full_research_v9_pipeline("./data/historical", "research_v9_data_and_parity_audit.md")
        return

    if args.run_research_v10:
        from backtest.research_v10.pipeline import run_full_research_v10_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V10 REAL MARKET DATA & PORTFOLIO DRAWDOWN GUARD ENGINE...")
        print("=" * 80)
        res = run_full_research_v10_pipeline("./data/historical", "research_v10_real_data_and_drawdown_report.md")
        return

    if args.run_research_v11:
        from backtest.research_v11.pipeline import run_full_research_v11_pipeline
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 RESEARCH V11 ORDER BOOK FEATURE TRANSFORMER & LEAKAGE AUDITOR ENGINE...")
        print("=" * 80)
        res = run_full_research_v11_pipeline("./data/historical", "research_v11_true_order_book_alpha_report.md")
        return









    if args.run_testnet_certification:
        from testnet_certifier import run_testnet_operational_certification
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 TESTNET OPERATIONS & CHAOS CERTIFICATION...")
        print("=" * 80)
        report_md = run_testnet_operational_certification("testnet_certification_report.md")
        print("\n" + report_md.encode('ascii', errors='ignore').decode('ascii'))
        return

    if args.run_testnet_soak:
        from testnet_soak_runner import run_testnet_soak_validation
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 REAL TESTNET OPERATIONAL VALIDATION & SOAK...")
        print("=" * 80)
        res = run_testnet_soak_validation(soak_hours=args.soak_hours)
        return

    t0 = time.time()
    candles = load_candles(args)
    print(f"Loaded {len(candles)} candles in {time.time()-t0:.1f}s.")
    if len(candles) < 200:
        print("WARNING: fewer than 200 candles — results will not be statistically meaningful.")

    if args.run_regime_research:
        from backtest.regime_research import (
            extract_regime_dataset,
            run_regime_bucket_analysis,
            evaluate_regime_hypothesis_oos,
        )

        print("\n" + "=" * 80)
        print("1. RUNNING REGIME RESEARCH & FEATURE VECTOR EXTRACTION...")
        print("=" * 80)
        out_csv = os.path.join(args.out_dir, "regime_trade_dataset.csv")
        df_dataset = extract_regime_dataset(candles, args.symbol, settings_obj, out_csv_path=out_csv)

        print("\n" + "=" * 80)
        print("2. RUNNING PREDEFINED FEATURE BUCKET HYPOTHESIS TEST...")
        print("=" * 80)
        bucket_md = run_regime_bucket_analysis(df_dataset)
        bucket_report_path = os.path.join(args.out_dir, "regime_bucket_analysis.md")
        with open(bucket_report_path, "w", encoding="utf-8") as f:
            f.write(bucket_md)
        print(bucket_md)

        print("\n" + "=" * 80)
        print("3. RUNNING FROZEN OUT-OF-SAMPLE (OOS) REGIME HYPOTHESIS VALIDATION...")
        print("=" * 80)
        oos_regime_md = evaluate_regime_hypothesis_oos(candles, args.symbol, settings_obj)
        oos_report_path = os.path.join(args.out_dir, "regime_oos_validation.md")
        with open(oos_report_path, "w", encoding="utf-8") as f:
            f.write(oos_regime_md)
        print(oos_regime_md)

        print(f"\nSaved Bucket Analysis Report to: {bucket_report_path}")
        print(f"Saved OOS Regime Validation Report to: {oos_report_path}")
        return

    if args.run_sensitivity_matrix:
        from backtest.validation import run_execution_sensitivity_matrix
        import pandas as pd
        df_15m = pd.DataFrame(candles, columns=["ts", "open", "high", "low", "close", "volume"])
        dt_idx = pd.to_datetime(df_15m["ts"], unit="ms", utc=True)
        df_1h = df_15m.set_index(dt_idx).resample("1h").agg({
            "ts": "first", "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna()
        candles_1h = df_1h[["ts", "open", "high", "low", "close", "volume"]].values.tolist()

        cand_c_settings = dataclasses.replace(settings_obj, timeframe="1h", min_volume_ratio=0.7, min_confidence_score=90)
        print("\n" + "=" * 80)
        print("RUNNING CANDIDATE C EXECUTION FRICTION SENSITIVITY MATRIX...")
        print("=" * 80)
        sens_md = run_execution_sensitivity_matrix(candles_1h, args.symbol, cand_c_settings)

        os.makedirs(args.out_dir, exist_ok=True)
        sens_report_path = os.path.join(args.out_dir, "execution_sensitivity_report.md")
        with open(sens_report_path, "w", encoding="utf-8") as f:
            f.write(sens_md)

        print(sens_md)
        print(f"\nSaved Sensitivity Report to: {sens_report_path}")
        return

    if args.run_frozen_oos:
        from backtest.validation import run_frozen_oos_evaluation
        cand_c_settings = dataclasses.replace(settings_obj, timeframe="1h", min_volume_ratio=0.7, min_confidence_score=90)
        print("\n" + "=" * 80)
        print("RUNNING FROZEN OUT-OF-SAMPLE (OOS) TEMPORAL HOLDOUT EVALUATION...")
        print("=" * 80)
        oos_md = run_frozen_oos_evaluation(candles, args.symbol, cand_c_settings)

        os.makedirs(args.out_dir, exist_ok=True)
        oos_report_path = os.path.join(args.out_dir, "frozen_oos_report.md")
        with open(oos_report_path, "w", encoding="utf-8") as f:
            f.write(oos_md)

        print(oos_md)
        print(f"\nSaved Frozen OOS Report to: {oos_report_path}")
        return

    if args.run_candidates:
        from backtest.validation import run_candidate_comparison
        print("\n" + "=" * 80)
        print("RUNNING CANDIDATE COMPARISON MATRIX (CANDIDATES A, B, C)...")
        print("=" * 80)
        cand_md = run_candidate_comparison(candles, args.symbol, settings_obj)

        os.makedirs(args.out_dir, exist_ok=True)
        cand_report_path = os.path.join(args.out_dir, "candidate_comparison_report.md")
        with open(cand_report_path, "w", encoding="utf-8") as f:
            f.write(cand_md)

        print(cand_md)
        print(f"\nSaved Candidate Comparison Report to: {cand_report_path}")
        return

    if args.run_v2_experiments:
        from backtest.validation import run_v2_experiment_series
        print("\n" + "=" * 80)
        print("RUNNING NEXUS-7 PULLBACK V2 EXPERIMENT SERIES (EXPERIMENTS A -> E)...")
        print("=" * 80)
        exp_md = run_v2_experiment_series(candles, args.symbol, settings_obj)

        os.makedirs(args.out_dir, exist_ok=True)
        exp_report_path = os.path.join(args.out_dir, "v2_experiment_report.md")
        with open(exp_report_path, "w", encoding="utf-8") as f:
            f.write(exp_md)

        print(exp_md)
        print(f"\nSaved Experiment Report to: {exp_report_path}")
        return

    if args.validate:
        from backtest.validation import run_full_validation_suite
        print("\n" + "=" * 80)
        print("RUNNING INSTITUTIONAL STRATEGY VALIDATION SUITE...")
        print("=" * 80)
        report_md = run_full_validation_suite(candles, args.symbol, settings_obj)

        os.makedirs(args.out_dir, exist_ok=True)
        val_report_path = os.path.join(args.out_dir, "validation_report.md")
        with open(val_report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        # Write to artifact dir as well
        artifact_dir = r"C:\Users\Administrator\.gemini\antigravity\brain\24820acc-97ef-4e5f-a49f-ed575fad8dcf"
        if os.path.exists(artifact_dir):
            art_val_path = os.path.join(artifact_dir, "validation_report.md")
            with open(art_val_path, "w", encoding="utf-8") as f:
                f.write(report_md)

        print(report_md)
        print(f"\nSaved Validation Report to: {val_report_path}")
        return

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

        if args.trace_trade is not None:
            trace_trade(report, args.trace_trade, candles)

    if len(reports) > 1:
        print_comparison(reports)


def trace_trade(report, trade_id: int, candles: list):
    from datetime import datetime, timezone
    if not report.trades:
        print("No trades were generated during this backtest run.")
        return
    if trade_id < 1 or trade_id > len(report.trades):
        print(f"Invalid trade_id {trade_id}. Total trades generated: {len(report.trades)}")
        return

    trade = report.trades[trade_id - 1]
    dt_entry = datetime.fromtimestamp(trade.entry_time_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    dt_exit = datetime.fromtimestamp(trade.exit_time_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if trade.exit_time_ms else "N/A"

    print("\n" + "=" * 80)
    print(f" TRADE TRACE DIAGNOSTIC REPORT: Trade #{trade_id} / {len(report.trades)}")
    print("=" * 80)
    print(f" Symbol:                   {trade.symbol}")
    print(f" Entry Bar Index:          {trade.entry_index}")
    print(f" Entry Timestamp:          {dt_entry} ({trade.entry_time_ms} ms)")
    print(f" Entry Fill Price:         ${trade.entry_price:,.2f}")
    print(f" Position Quantity:        {trade.quantity:.6f} units")
    print(f" Initial Risk USD:         ${trade.risk_usd:,.2f}")
    print(f" AI Confidence Score:      {trade.ai_confidence if trade.ai_confidence is not None else 'N/A'}")
    print("-" * 80)
    print(f" Stop Loss Level:          ${trade.stop_loss:,.2f}")
    print(f" Take Profit Target:       ${trade.take_profit:,.2f}")
    if trade.tp1_price:
        print(f" TP Tranche 1 Target:      ${trade.tp1_price:,.2f}")
    if trade.tp2_price:
        print(f" TP Tranche 2 Target:      ${trade.tp2_price:,.2f}")
    print("-" * 80)
    print(f" Exit Bar Index:           {trade.exit_index}")
    print(f" Exit Timestamp:           {dt_exit} ({trade.exit_time_ms} ms)")
    print(f" Exit Fill Price:          ${trade.exit_price:,.2f}" if trade.exit_price else " Exit Fill Price: N/A")
    print(f" Exit Reason:              {trade.exit_reason}")
    print(f" Total Fees Paid:          ${trade.fees_usd:,.2f}")
    print(f" Total Slippage Cost:      ${trade.slippage_usd:,.2f}")
    print(f" Net Realized PnL:         ${trade.pnl_usd:,.2f} ({trade.r_multiple:+.2f}R)")
    print("=" * 80)


if __name__ == "__main__":
    main()

