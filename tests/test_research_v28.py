"""
NEXUS-7 — RESEARCH V28 UNIT TEST SUITE
Tests multi-asset data pipeline, strategy library, zero-stub candle resolver,
forensic anti-stub integrity, statistical evaluator, expectancy frontier, and full pipeline.
"""
import os
import pytest
import pandas as pd
import numpy as np

from backtest.research_v28.data_pipeline import (
    generate_synthetic_ohlcv,
    load_multi_asset_dataset,
    split_chronological_dataset
)
from backtest.research_v28.strategy_library import (
    VolatilityBreakoutTrend,
    MultiTimeframeStructurePullback,
    RegimeAdaptiveMeanReversion,
    MomentumSqueezeContinuation,
    DynamicVolatilityConfluenceFilter
)
from backtest.research_v28.candle_resolver import (
    resolve_trade_trajectories,
    compute_trade_ledger_and_equity
)
from backtest.research_v28.statistical_evaluator import (
    evaluate_trade_ledger,
    compute_bootstrap_pnl_ci,
    check_v28_statistical_gates
)
from backtest.research_v28.expectancy_frontier import (
    build_expectancy_frontier,
    evaluate_risk_budget_tiers
)
from backtest.research_v28.engine import run_full_v28_pipeline


def test_v28_data_pipeline():
    df = generate_synthetic_ohlcv(symbol="BTC/USDT", timeframe="30m", days=30, seed=42)
    assert not df.empty
    assert len(df) > 100
    assert "timestamp" in df.columns
    assert "close" in df.columns

    df_tr, df_v, df_fw = split_chronological_dataset(df)
    assert len(df_tr) + len(df_v) + len(df_fw) == len(df)
    assert len(df_tr) == int(len(df) * 0.50)


def test_v28_strategy_library():
    df = generate_synthetic_ohlcv(symbol="ETH/USDT", timeframe="30m", days=30, seed=42)
    cand = VolatilityBreakoutTrend(timeframe="30m", min_confidence=0.80)
    signals = cand.generate_signals(df)
    assert isinstance(signals, list)

    for s in signals:
        assert "side" in s
        assert "price" in s
        assert "confidence" in s
        assert s["confidence"] >= 0.80


def test_v28_candle_resolver():
    df = generate_synthetic_ohlcv(symbol="SOL/USDT", timeframe="30m", days=30, seed=42)
    cand = VolatilityBreakoutTrend(timeframe="30m", min_confidence=0.80)
    signals = cand.generate_signals(df)

    resolved, _ = resolve_trade_trajectories(
        signals=signals,
        df=df,
        symbol="SOL/USDT",
        initial_balance=10000.0,
        risk_per_trade_pct=0.005,
        fee_pct=0.0015,
        slippage_pct=0.0005
    )
    assert isinstance(resolved, list)

    trade_ledger, equity_curve = compute_trade_ledger_and_equity(resolved, initial_balance=10000.0)
    assert len(equity_curve) == len(trade_ledger) + 1

    for t in trade_ledger:
        assert "net_pnl" in t
        assert "fees" in t
        assert "drawdown_pct" in t
        assert t["outcome"] in ["WIN", "LOSS"]


def test_v28_forensic_anti_stub():
    """
    CRITICAL FORENSIC TEST:
    Verifies that trade outcomes are strictly independent of signal confidence, candidate_id, or any non-candle variable.
    Reversing the candle trajectory must invert the outcome from WIN to LOSS or vice versa.
    """
    timestamps = [pd.Timestamp("2026-01-01 00:00:00") + pd.Timedelta(minutes=30 * i) for i in range(10)]

    # Upward candle trajectory
    bullish_df = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
        "high": [100.5, 101.5, 102.5, 103.5, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
        "low": [99.5, 100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5],
        "close": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
        "volume": [1000.0] * 10
    })

    # High confidence signal
    high_conf_sig = [{
        "timestamp": timestamps[0],
        "price": 100.0,
        "stop_loss": 98.0,
        "take_profit": 105.0,
        "confidence": 0.99,  # High confidence
        "candidate_id": "TEST-CANDIDATE"
    }]

    # Resolve on bullish df -> Should hit Take Profit (WIN)
    res_bull, _ = resolve_trade_trajectories(high_conf_sig, bullish_df, symbol="TEST/USDT")
    assert len(res_bull) == 1
    assert res_bull[0]["outcome"] == "WIN"

    # Downward candle trajectory with SAME signal and SAME high confidence (0.99)
    bearish_df = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 94.0, 93.0, 92.0, 91.0],
        "high": [100.5, 99.5, 98.5, 97.5, 96.5, 95.5, 94.5, 93.5, 92.5, 91.5],
        "low": [99.5, 98.0, 97.0, 96.0, 95.0, 94.0, 93.0, 92.0, 91.0, 90.0],
        "close": [99.0, 98.0, 97.0, 96.0, 95.0, 94.0, 93.0, 92.0, 91.0, 90.0],
        "volume": [1000.0] * 10
    })

    # Resolve on bearish df -> MUST hit Stop Loss (LOSS) despite 0.99 confidence
    res_bear, _ = resolve_trade_trajectories(high_conf_sig, bearish_df, symbol="TEST/USDT")
    assert len(res_bear) == 1
    assert res_bear[0]["outcome"] == "LOSS"
    assert res_bear[0]["exit_reason"] == "STOP_LOSS"


def test_v28_statistical_evaluator():
    dummy_trades = [
        {"net_pnl": 100.0, "drawdown_pct": 0.5},
        {"net_pnl": -50.0, "drawdown_pct": 1.2},
        {"net_pnl": 120.0, "drawdown_pct": 0.8},
    ] * 10

    metrics = evaluate_trade_ledger(dummy_trades, total_days=20.0)
    assert metrics["total_trades"] == 30
    assert metrics["profit_factor"] == 4.4

    ci_mean, ci_lower, ci_upper = compute_bootstrap_pnl_ci(metrics["net_pnls"], num_iterations=100)
    assert ci_lower > 0.0

    gates_eval = check_v28_statistical_gates(metrics, (ci_mean, ci_lower, ci_upper))
    assert "verdict" in gates_eval


def test_v28_expectancy_frontier():
    dummy_resolved = [
        {
            "symbol": "BTC/USDT", "candidate_id": "V28-TEST",
            "entry_timestamp": f"2026-01-01 10:{i:02d}:00",
            "entry_price": 100.0, "exit_price": 105.0 if i % 2 == 0 else 98.0,
            "risk_per_unit": 2.0
        }
        for i in range(10)
    ]
    trade_ledger, _ = compute_trade_ledger_and_equity(dummy_resolved, initial_balance=10000.0)

    risk_tiers = evaluate_risk_budget_tiers(trade_ledger, initial_balance=10000.0)
    assert "risk_0.25pct" in risk_tiers
    assert "risk_0.50pct" in risk_tiers
    assert "risk_0.75pct" in risk_tiers


def test_v28_full_pipeline_execution():
    res = run_full_v28_pipeline(days=30, seed=42)
    assert "overall_verdict" in res
    assert "eval_results" in res
    assert os.path.exists("strategy_research/v28_expectancy_summary.csv")
    assert os.path.exists("strategy_research/V28_EXPECTANCY_FRONTIER_REPORT.md")
