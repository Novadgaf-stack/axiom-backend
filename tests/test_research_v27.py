"""
NEXUS-7 — RESEARCH V27 UNIT TEST SUITE
Tests strategy library, multi-asset data pipeline, 50/25/25 chronological splitting,
bootstrap CIs, statistical gates, risk budget evaluator, forward paper trading engine, and full pipeline.
"""
import os
import pytest
import pandas as pd

from backtest.research_v27.strategy_library import (
    SUPPORTED_PAIRS,
    TIMEFRAMES,
    TargetedMTFPullback,
    FilteredBreakoutExpansion,
    AdaptiveMeanReversion,
    MomentumContinuation,
    DynamicConfluenceFilter
)
from backtest.research_v27.data_pipeline import (
    generate_synthetic_ohlcv,
    load_multi_asset_dataset,
    split_chronological_dataset
)
from backtest.research_v27.statistical_gates import (
    evaluate_trade_sequence,
    compute_bootstrap_ci,
    check_statistical_gates
)
from backtest.research_v27.risk_evaluator import evaluate_risk_sizing_sensitivity
from backtest.research_v27.forward_paper_engine import AcceleratedForwardPaperEngine
from backtest.research_v27.engine import run_full_v27_pipeline


def test_v27_data_pipeline():
    df = generate_synthetic_ohlcv(symbol="BTC/USDT", timeframe="15m", days=30, seed=42)
    assert not df.empty
    assert len(df) > 100
    assert "timestamp" in df.columns
    assert "close" in df.columns

    df_tr, df_v, df_fw = split_chronological_dataset(df)
    assert len(df_tr) + len(df_v) + len(df_fw) == len(df)
    assert len(df_tr) == int(len(df) * 0.50)


def test_v27_strategy_library():
    df = generate_synthetic_ohlcv(symbol="ETH/USDT", timeframe="15m", days=30, seed=42)
    cand = TargetedMTFPullback(timeframe="15m", min_confidence=0.80)
    signals = cand.generate_signals(df)
    assert isinstance(signals, list)

    for s in signals:
        assert "side" in s
        assert "price" in s
        assert "confidence" in s
        assert s["confidence"] >= 0.80


def test_v27_statistical_gates():
    dummy_trades = [
        {"price": 100.0, "stop_loss": 98.0, "take_profit": 104.0, "outcome": "WIN", "confidence": 0.85},
        {"price": 100.0, "stop_loss": 98.0, "take_profit": 104.0, "outcome": "LOSS", "confidence": 0.80},
        {"price": 100.0, "stop_loss": 98.0, "take_profit": 104.0, "outcome": "WIN", "confidence": 0.85},
    ] * 10

    metrics = evaluate_trade_sequence(dummy_trades, total_days=20.0, friction_pct=0.0015)
    assert metrics["total_trades"] == 30
    assert metrics["trades_per_day"] == 1.5

    ci_mean, ci_lower, ci_upper = compute_bootstrap_ci(metrics["returns"], num_iterations=100)
    assert isinstance(ci_lower, float)
    assert isinstance(ci_upper, float)

    gates_eval = check_statistical_gates(metrics, (ci_mean, ci_lower, ci_upper))
    assert "overall_pass" in gates_eval
    assert "verdict" in gates_eval


def test_v27_risk_evaluator():
    dummy_trades = [
        {"timestamp": "2026-01-01 10:00:00", "outcome": "WIN", "confidence": 0.85},
        {"timestamp": "2026-01-01 14:00:00", "outcome": "LOSS", "confidence": 0.80},
        {"timestamp": "2026-01-02 10:00:00", "outcome": "WIN", "confidence": 0.85},
    ]
    risk_res = evaluate_risk_sizing_sensitivity(dummy_trades, initial_balance=10000.0)
    assert "risk_0.5pct" in risk_res
    assert "risk_0.7pct" in risk_res or "risk_0.75pct" in risk_res
    assert "risk_1.0pct" in risk_res


def test_v27_forward_paper_engine():
    dataset = load_multi_asset_dataset(days=30, seed=42)
    cand = DynamicConfluenceFilter(timeframe="30m", min_confidence=0.80)
    paper_sim = AcceleratedForwardPaperEngine(cand, initial_balance=10000.0, risk_per_trade_pct=0.5)

    res = paper_sim.run_forward_paper_trading(dataset)
    assert "total_return_pct" in res
    assert "telemetry" in res
    assert res["telemetry"]["signals_generated"] >= 0


def test_v27_full_pipeline_execution():
    res = run_full_v27_pipeline(days=30, seed=42)
    assert "overall_verdict" in res
    assert "summary_results" in res
    assert os.path.exists("strategy_research/v27_expectancy_summary.csv")
    assert os.path.exists("strategy_research/V27_EXPECTANCY_AND_PAPER_TRADING_REPORT.md")


def test_v27_forensic_audit_execution():
    from backtest.research_v27.forensic_audit import run_forensic_audit
    res = run_forensic_audit(days=30, seed=42)
    assert "verdict" in res
    assert res["verdict"] in ["V27_INVALIDATED", "V27_INDEPENDENTLY_VERIFIED"]
    assert "true_metrics" in res
    assert "bootstrap_results" in res
    assert os.path.exists("strategy_research/V27_FORENSIC_AUDIT_REPORT.md")

