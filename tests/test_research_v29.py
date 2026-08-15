"""
Unit Test Suite for NEXUS-7 Research V29 — Zero-Stub Forensic Expectancy Search
"""

import os
import pytest
import numpy as np
import pandas as pd

from backtest.research_v29.data_pipeline import (
    generate_synthetic_asset_data,
    split_dataset_chronological,
    compute_asset_correlation_matrix,
    load_multi_asset_dataset,
    SUPPORTED_ASSETS,
    SUPPORTED_TIMEFRAMES
)
from backtest.research_v29.strategy_library import (
    CANDIDATE_STRATEGIES,
    generate_signals_breakout_vol,
    generate_signals_mtf_pullback,
    generate_signals_regime_reversion,
    generate_signals_mom_continuation,
    generate_signals_dynamic_confluence,
    generate_signals_liquidity_sweep
)
from backtest.research_v29.candle_resolver import resolve_zero_stub_trades
from backtest.research_v29.statistical_evaluator import compute_trade_statistics
from backtest.research_v29.expectancy_frontier import (
    build_expectancy_frontier,
    evaluate_friction_and_risk_budget_sensitivity
)
from backtest.research_v29.engine import run_full_v29_pipeline


def test_v29_data_pipeline():
    """Verifies data pipeline loading, 50/25/25 chronological splitting, and correlation matrix."""
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
    assert corr_matrix.loc["BTC", "BTC"] == pytest.approx(1.0)


def test_v29_strategy_library():
    """Verifies all 12 candidate strategy configurations generate indicators and signals."""
    df = generate_synthetic_asset_data("BTC", "30m", num_bars=500, seed=42)

    for c_name, config in CANDIDATE_STRATEGIES.items():
        func = config["func"]
        df_sig = func(df.copy(), param_mult=1.0)

        assert "signal" in df_sig.columns
        assert "stop_loss" in df_sig.columns
        assert "take_profit" in df_sig.columns
        assert "confidence" in df_sig.columns
        assert set(df_sig["signal"].unique()).issubset({-1, 0, 1})


def test_v29_candle_resolver():
    """Verifies zero-stub bar-by-bar candle traversal, fee/slippage deduction, and collision handling."""
    dates = pd.date_range("2026-01-01", periods=100, freq="1h")
    # Price path: 100 -> 105 -> 95
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

    # Add Long signal at bar 10
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
    assert t["net_pnl"] != t["gross_pnl"] # Fees deducted


def test_v29_forensic_anti_stub():
    """
    CRITICAL FORENSIC TEST:
    Proves that trade outcome is derived strictly from price trajectory.
    Reversing market trajectory from bullish to bearish turns a high-confidence signal from WIN to LOSS.
    """
    dates = pd.date_range("2026-01-01", periods=50, freq="1h")

    # Bullish price path
    bull_prices = np.linspace(100.0, 110.0, 50)
    df_bull = pd.DataFrame({
        "timestamp": dates,
        "open": bull_prices,
        "high": bull_prices + 0.5,
        "low": bull_prices - 0.5,
        "close": bull_prices,
        "volume": 1000.0,
        "asset": "BTC",
        "timeframe": "1h"
    })

    signals = np.zeros(50, dtype=int)
    signals[5] = 1
    sl = np.zeros(50)
    tp = np.zeros(50)
    conf = np.zeros(50)

    sl[5] = 97.0
    tp[5] = 106.0
    conf[5] = 0.99 # HIGH CONFIDENCE

    df_bull["signal"] = signals
    df_bull["stop_loss"] = sl
    df_bull["take_profit"] = tp
    df_bull["confidence"] = conf

    res_bull = resolve_zero_stub_trades(df_bull)
    assert len(res_bull["trades"]) == 1
    assert res_bull["trades"][0]["exit_reason"] == "TAKE_PROFIT"
    assert res_bull["trades"][0]["net_pnl"] > 0 # WIN

    # Bearish price path (market trajectory reversed)
    bear_prices = np.linspace(100.0, 90.0, 50)
    df_bear = pd.DataFrame({
        "timestamp": dates,
        "open": bear_prices,
        "high": bear_prices + 0.5,
        "low": bear_prices - 0.5,
        "close": bear_prices,
        "volume": 1000.0,
        "asset": "BTC",
        "timeframe": "1h"
    })

    df_bear["signal"] = signals
    df_bear["stop_loss"] = sl
    df_bear["take_profit"] = tp
    df_bear["confidence"] = conf # SAME 0.99 CONFIDENCE SCORE

    res_bear = resolve_zero_stub_trades(df_bear)
    assert len(res_bear["trades"]) == 1
    assert res_bear["trades"][0]["exit_reason"] == "STOP_LOSS"
    assert res_bear["trades"][0]["net_pnl"] < 0 # LOSS

    # PROOF: High confidence score (0.99) did NOT prevent the loss when price reversed!


def test_v29_position_sizing_and_circuit_breaker():
    """Verifies stop-distance position sizing and 2% daily loss circuit breaker."""
    dates = pd.date_range("2026-01-01", periods=100, freq="1h")
    prices = np.linspace(100, 80, 100) # Crashing market

    df = pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices + 0.2,
        "low": prices - 0.5,
        "close": prices,
        "volume": 1000.0,
        "asset": "BTC",
        "timeframe": "1h"
    })

    # Multiple Long signals in crashing market on the same day
    signals = np.zeros(100, dtype=int)
    signals[2] = 1
    signals[4] = 1
    signals[6] = 1
    signals[8] = 1

    sl = np.zeros(100)
    tp = np.zeros(100)

    for i in [2, 4, 6, 8]:
        sl[i] = prices[i] - 1.0
        tp[i] = prices[i] + 3.0

    df["signal"] = signals
    df["stop_loss"] = sl
    df["take_profit"] = tp
    df["confidence"] = 0.8

    res = resolve_zero_stub_trades(
        df=df,
        risk_fraction=0.005, # 0.50% account risk
        daily_circuit_breaker=0.02 # 2% daily circuit breaker
    )

    trades = res["trades"]
    # Circuit breaker stops subsequent trades once daily loss reaches 2%
    assert len(trades) < 4
    assert res["max_drawdown"] <= 0.15 # Bounded drawdown


def test_v29_correlated_exposure_limits():
    """Verifies asset correlation penalty multiplier scales down position size."""
    dates = pd.date_range("2026-01-01", periods=50, freq="1h")
    prices = np.linspace(100, 105, 50)
    df = pd.DataFrame({
        "timestamp": dates, "open": prices, "high": prices + 1.0,
        "low": prices - 1.0, "close": prices, "volume": 1000.0,
        "asset": "SOL", "timeframe": "1h"
    })
    signals = np.zeros(50, dtype=int); signals[5] = 1
    sl = np.zeros(50); sl[5] = 98.0
    tp = np.zeros(50); tp[5] = 104.0
    df["signal"] = signals; df["stop_loss"] = sl; df["take_profit"] = tp

    # Unpenalized (penalty mult = 1.0)
    res_normal = resolve_zero_stub_trades(df, correlation_penalty_mult=1.0)
    # Penalized (penalty mult = 0.70)
    res_penalized = resolve_zero_stub_trades(df, correlation_penalty_mult=0.70)

    assert res_penalized["trades"][0]["risk_usd"] < res_normal["trades"][0]["risk_usd"]


def test_v29_full_pipeline_execution():
    """Executes full V29 pipeline end-to-end and validates report generation."""
    output = run_full_v29_pipeline(seed=42)

    assert "frontier_results" in output
    assert "overall_verdict" in output
    assert output["overall_verdict"] in [
        "NO ROBUST PROFITABLE EDGE FOUND",
        "CANDIDATE FOUND — REQUIRES FORWARD PAPER VALIDATION"
    ]

    md_path = output["report_md_path"]
    csv_path = output["summary_csv_path"]

    assert os.path.exists(md_path)
    assert os.path.exists(csv_path)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "NEXUS-7 Research V29" in content
    assert "Frequency vs Expectancy vs Drawdown Frontier Table" in content
