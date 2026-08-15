"""
Unit Test Suite for NEXUS-7 Research V30 — Robust ~1 Trade/Day Profitability Research
"""

import os
import pytest
import numpy as np
import pandas as pd

from backtest.research_v30.data_pipeline import (
    generate_synthetic_asset_data,
    split_dataset_chronological,
    compute_asset_correlation_matrix,
    get_asset_holdout_split,
    load_multi_asset_dataset,
    SUPPORTED_ASSETS,
    SUPPORTED_TIMEFRAMES
)
from backtest.research_v30.strategy_library import (
    CANDIDATE_STRATEGIES,
    generate_signals_regime_trend,
    generate_signals_breakout_vol,
    generate_signals_pullback_cont,
    generate_signals_liquidity_reversal,
    generate_signals_mtf_confluence,
    generate_signals_vol_adaptive
)
from backtest.research_v30.candle_resolver import resolve_zero_stub_trades
from backtest.research_v30.statistical_evaluator import compute_trade_statistics
from backtest.research_v30.position_sizing import evaluate_position_sizing_tiers
from backtest.research_v30.walk_forward import run_walk_forward_validation
from backtest.research_v30.robustness import (
    run_parameter_stability_test,
    run_friction_and_execution_stress_test
)
from backtest.research_v30.monte_carlo import run_monte_carlo_resampling
from backtest.research_v30.expectancy_frontier import build_expectancy_frontier
from backtest.research_v30.engine import run_full_v30_pipeline


def test_v30_data_pipeline():
    """Verifies data pipeline loading, 50/25/25 chronological splitting, asset holdouts, and correlation matrix."""
    df = generate_synthetic_asset_data(asset="BTC", timeframe="1h", num_bars=1000, seed=42)
    assert len(df) == 1000
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume", "asset", "timeframe"]

    train, val, oos = split_dataset_chronological(df, train_ratio=0.50, val_ratio=0.25, oos_ratio=0.25)
    assert len(train) == 500
    assert len(val) == 250
    assert len(oos) == 250
    assert train["timestamp"].iloc[-1] < val["timestamp"].iloc[0]
    assert val["timestamp"].iloc[-1] < oos["timestamp"].iloc[0]

    asset_data = {
        "BTC": df,
        "ETH": generate_synthetic_asset_data("ETH", "1h", num_bars=1000, seed=43)
    }
    corr_matrix = compute_asset_correlation_matrix(asset_data)
    assert "BTC" in corr_matrix.columns
    assert "ETH" in corr_matrix.columns

    train_assets, holdout_assets = get_asset_holdout_split(holdout_ratio=0.25, seed=42)
    assert len(holdout_assets) > 0
    assert len(train_assets) + len(holdout_assets) == len(SUPPORTED_ASSETS)


def test_v30_strategy_library():
    """Verifies all 14 candidate strategy configurations generate valid indicators and signals."""
    df = generate_synthetic_asset_data("BTC", "30m", num_bars=500, seed=42)

    for c_name, config in CANDIDATE_STRATEGIES.items():
        func = config["func"]
        df_sig = func(df.copy(), param_mult=1.0)

        assert "signal" in df_sig.columns
        assert "stop_loss" in df_sig.columns
        assert "take_profit" in df_sig.columns
        assert "confidence" in df_sig.columns
        assert set(df_sig["signal"].unique()).issubset({-1, 0, 1})


def test_v30_candle_resolver():
    """Verifies zero-stub bar-by-bar candle traversal, fee/slippage deduction, and collision handling."""
    dates = pd.date_range("2026-01-01", periods=100, freq="1h")
    prices = np.linspace(100, 105, 50).tolist() + np.linspace(105, 95, 50).tolist()

    df = pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": 1000.0,
        "asset": "BTC",
        "timeframe": "1h"
    })

    signals = np.zeros(100, dtype=int)
    signals[10] = 1
    stop_loss = np.zeros(100)
    take_profit = np.zeros(100)
    confidence = np.zeros(100)

    stop_loss[10] = 98.0
    take_profit[10] = 104.0
    confidence[10] = 0.85

    df["signal"] = signals
    df["stop_loss"] = stop_loss
    df["take_profit"] = take_profit
    df["confidence"] = confidence

    res = resolve_zero_stub_trades(
        df=df,
        risk_fraction=0.005,
        fee_rate=0.0015,
        slippage=0.0005,
        execution_delay=1,
        initial_balance=1000.0
    )

    trades = res["trades"]
    assert len(trades) >= 1
    t = trades[0]
    assert t["direction"] == "LONG"
    assert t["entry_price"] > 0.0
    assert t["total_fee"] > 0.0
    assert t["net_pnl"] != t["gross_pnl"]


def test_v30_forensic_anti_stub():
    """
    CRITICAL FORENSIC ANTI-STUB TEST:
    Explicitly proves that:
    1. confidence = 0.99 + adverse price path -> LOSS
    2. confidence = 0.50 + favorable price path -> WIN
    """
    dates = pd.date_range("2026-01-01", periods=50, freq="1h")

    # Case 1: High confidence (0.99) + Bearish adverse price path
    bear_prices = np.linspace(100.0, 90.0, 50)
    df_bear = pd.DataFrame({
        "timestamp": dates, "open": bear_prices, "high": bear_prices + 0.5,
        "low": bear_prices - 0.5, "close": bear_prices, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })
    sig1 = np.zeros(50, dtype=int); sig1[5] = 1
    sl1 = np.zeros(50); sl1[5] = 97.0
    tp1 = np.zeros(50); tp1[5] = 106.0
    conf1 = np.zeros(50); conf1[5] = 0.99 # HIGH CONFIDENCE

    df_bear["signal"] = sig1; df_bear["stop_loss"] = sl1; df_bear["take_profit"] = tp1; df_bear["confidence"] = conf1

    res_case1 = resolve_zero_stub_trades(df_bear)
    assert len(res_case1["trades"]) == 1
    assert res_case1["trades"][0]["exit_reason"] == "STOP_LOSS"
    assert res_case1["trades"][0]["net_pnl"] < 0 # PROOF: LOSS despite 0.99 confidence

    # Case 2: Low confidence (0.50) + Bullish favorable price path
    bull_prices = np.linspace(100.0, 110.0, 50)
    df_bull = pd.DataFrame({
        "timestamp": dates, "open": bull_prices, "high": bull_prices + 0.5,
        "low": bull_prices - 0.5, "close": bull_prices, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })
    sig2 = np.zeros(50, dtype=int); sig2[5] = 1
    sl2 = np.zeros(50); sl2[5] = 97.0
    tp2 = np.zeros(50); tp2[5] = 106.0
    conf2 = np.zeros(50); conf2[5] = 0.50 # LOW CONFIDENCE

    df_bull["signal"] = sig2; df_bull["stop_loss"] = sl2; df_bull["take_profit"] = tp2; df_bull["confidence"] = conf2

    res_case2 = resolve_zero_stub_trades(df_bull)
    assert len(res_case2["trades"]) == 1
    assert res_case2["trades"][0]["exit_reason"] == "TAKE_PROFIT"
    assert res_case2["trades"][0]["net_pnl"] > 0 # PROOF: WIN despite 0.50 confidence


def test_v30_position_sizing_and_risk_budgets():
    """Verifies position sizing tiers, 2% daily loss circuit breaker, and risk budget cap when PF <= 1.00."""
    dates = pd.date_range("2026-01-01", periods=100, freq="1h")
    prices = np.linspace(100, 80, 100) # Crashing market

    df = pd.DataFrame({
        "timestamp": dates, "open": prices, "high": prices + 0.2,
        "low": prices - 0.5, "close": prices, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })

    signals = np.zeros(100, dtype=int)
    signals[2] = 1; signals[4] = 1; signals[6] = 1; signals[8] = 1
    sl = np.zeros(100); tp = np.zeros(100)

    for i in [2, 4, 6, 8]:
        sl[i] = prices[i] - 1.0
        tp[i] = prices[i] + 3.0

    df["signal"] = signals; df["stop_loss"] = sl; df["take_profit"] = tp; df["confidence"] = 0.8

    res = resolve_zero_stub_trades(df=df, risk_fraction=0.005, daily_circuit_breaker=0.02)
    assert len(res["trades"]) < 4 # Circuit breaker trips

    # Verify position sizing cap when PF <= 1.00
    sizing_results = evaluate_position_sizing_tiers(df)
    assert sizing_results["risk_100bps"]["stats"]["sizing_note"] == "CAP_ENFORCED (PF <= 1.00)"


def test_v30_walk_forward_and_monte_carlo():
    """Verifies walk-forward rolling window validation and Monte Carlo trade shuffling."""
    dates = pd.date_range("2026-01-01", periods=200, freq="1h")
    prices = np.linspace(100, 120, 200)

    df = pd.DataFrame({
        "timestamp": dates, "open": prices, "high": prices + 1.0,
        "low": prices - 0.5, "close": prices, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })
    signals = np.zeros(200, dtype=int)
    sl = np.zeros(200); tp = np.zeros(200)

    for idx in range(10, 190, 20):
        signals[idx] = 1
        sl[idx] = prices[idx] - 1.0
        tp[idx] = prices[idx] + 2.5

    df["signal"] = signals; df["stop_loss"] = sl; df["take_profit"] = tp

    wf_res = run_walk_forward_validation(df, num_windows=4)
    assert wf_res["num_windows"] == 4
    assert len(wf_res["window_results"]) == 4

    trades = resolve_zero_stub_trades(df)["trades"]
    mc_res = run_monte_carlo_resampling(trades, iterations=100)
    assert mc_res["iterations"] == 100
    assert "median_return_pct" in mc_res
    assert "dd_95th_percentile" in mc_res


def test_v30_parameter_stability_and_robustness():
    """Verifies parameter stability testing across neighboring parameter variations."""
    df = generate_synthetic_asset_data("BTC", "30m", num_bars=400, seed=42)
    stab_res = run_parameter_stability_test("V30-BREAKOUT-VOL-30M", generate_signals_breakout_vol, df)
    assert "is_stable" in stab_res
    assert len(stab_res["neighborhood_results"]) == 3


def test_v30_full_pipeline_execution():
    """Executes full V30 pipeline end-to-end and validates report generation."""
    output = run_full_v30_pipeline(seed=42)

    assert "frontier_results" in output
    assert "overall_verdict" in output
    assert output["overall_verdict"] in [
        "ROBUST_EDGE_FOUND",
        "PROMISING_BUT_INSUFFICIENT_SAMPLE",
        "FREQUENCY_EDGE_FOUND_BUT_UNPROFITABLE",
        "PROFITABLE_BUT_NOT_ROBUST",
        "NO_ROBUST_PROFITABLE_EDGE_FOUND"
    ]

    md_path = output["report_md_path"]
    csv_path = output["summary_csv_path"]

    assert os.path.exists(md_path)
    assert os.path.exists(csv_path)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "NEXUS-7 Research V30" in content
    assert "Frequency vs Expectancy vs Drawdown Frontier Table" in content
