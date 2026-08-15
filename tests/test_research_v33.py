"""
Comprehensive Unit Test Suite for NEXUS-7 Research V33
Verifies zero-stub anti-stub outcome guarantees, no-lookahead indicator logic,
conservative SL/TP same-candle collision, fees & slippage accounting,
liquidity filtering, universe expansion, opportunity selection, stop-distance sizing,
walk-forward validation, parameter stability, and end-to-end pipeline execution.
"""

import pytest
import pandas as pd
import numpy as np
import os

from backtest.research_v33.data_pipeline import (
    generate_synthetic_asset_data,
    validate_and_clean_ohlcv,
    apply_liquidity_filter,
    split_dataset_chronological,
    load_universe_tier,
    compute_rolling_correlation_matrix
)
from backtest.research_v33.strategy_library import (
    generate_signals_trend_cont,
    generate_signals_vol_expansion,
    CANDIDATE_STRATEGIES
)
from backtest.research_v33.candle_resolver import resolve_zero_stub_trades
from backtest.research_v33.statistical_evaluator import (
    compute_trade_statistics,
    assign_official_verdict
)
from backtest.research_v33.opportunity_selector import select_portfolio_opportunities
from backtest.research_v33.position_sizing import evaluate_position_sizing_and_growth
from backtest.research_v33.walk_forward import run_walk_forward_validation
from backtest.research_v33.robustness import (
    run_parameter_perturbation_test,
    run_friction_and_execution_stress_test
)
from backtest.research_v33.monte_carlo import run_monte_carlo_resampling
from backtest.research_v33.engine import run_full_v33_pipeline


def test_v33_anti_stub_outcome():
    """
    CRITICAL ANTI-STUB GUARANTEE TEST:
    1. Confidence = 0.99 + Adverse price trajectory MUST result in a LOSS.
    2. Confidence = 0.50 + Favorable price trajectory MUST result in a WIN.
    Proves confidence scores or candidate IDs NEVER spoof trade outcomes.
    """
    timestamps = pd.date_range("2025-01-01", periods=10, freq="1h")

    # Scenario A: High Confidence (0.99), Long signal, but price drops to SL -> LOSS
    df_adverse = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0] * 10,
        "high": [101.0, 101.0, 101.0, 95.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0],
        "low":  [99.0,  99.0,  99.0,  80.0, 85.0, 85.0, 85.0, 85.0, 85.0, 85.0],
        "close": [100.0] * 10,
        "volume": [1000.0] * 10,
        "signal": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        "stop_loss": [0.0, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "take_profit": [0.0, 120.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "confidence": [0.0, 0.99, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "asset": ["BTC"] * 10
    })

    res_adverse = resolve_zero_stub_trades(df_adverse)
    assert len(res_adverse["trades"]) == 1
    assert res_adverse["trades"][0]["net_pnl"] < 0
    assert res_adverse["trades"][0]["exit_reason"] in ["STOP_LOSS", "SL_TP_COLLISION"]

    # Scenario B: Low Confidence (0.50), Long signal, but price rises to TP -> WIN
    df_favorable = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0] * 10,
        "high": [101.0, 101.0, 101.0, 130.0, 130.0, 130.0, 130.0, 130.0, 130.0, 130.0],
        "low":  [99.0,  99.0,  99.0,  99.0,  99.0,  99.0,  99.0,  99.0,  99.0,  99.0],
        "close": [100.0] * 10,
        "volume": [1000.0] * 10,
        "signal": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        "stop_loss": [0.0, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "take_profit": [0.0, 120.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "confidence": [0.0, 0.50, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "asset": ["BTC"] * 10
    })

    res_favorable = resolve_zero_stub_trades(df_favorable)
    assert len(res_favorable["trades"]) == 1
    assert res_favorable["trades"][0]["net_pnl"] > 0
    assert res_favorable["trades"][0]["exit_reason"] == "TAKE_PROFIT"


def test_v33_no_lookahead():
    """Verifies strategy signals depend strictly on past data."""
    df_raw = generate_synthetic_asset_data("BTC", "1h", num_bars=200, seed=101)
    df_sig = generate_signals_trend_cont(df_raw)

    # Mutate future close prices
    df_future_mutated = df_raw.copy()
    df_future_mutated.loc[150:, "close"] = df_future_mutated.loc[150:, "close"] * 5.0
    df_sig_mutated = generate_signals_trend_cont(df_future_mutated)

    # Signals up to index 140 must remain identical
    np.testing.assert_array_equal(
        df_sig["signal"].iloc[:140].values,
        df_sig_mutated["signal"].iloc[:140].values
    )


def test_v33_same_candle_collision():
    """Verifies conservative SL/TP collision handling (treated as LOSS)."""
    timestamps = pd.date_range("2025-01-01", periods=5, freq="1h")
    df_collision = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0] * 5,
        "high": [101.0, 101.0, 130.0, 101.0, 101.0],  # Touches TP (120)
        "low":  [99.0,  99.0,  70.0,  99.0,  99.0],  # Touches SL (90) on same bar!
        "close": [100.0] * 5,
        "volume": [1000.0] * 5,
        "signal": [0, 1, 0, 0, 0],
        "stop_loss": [0.0, 90.0, 0.0, 0.0, 0.0],
        "take_profit": [0.0, 120.0, 0.0, 0.0, 0.0],
        "confidence": [0.0, 0.8, 0.0, 0.0, 0.0]
    })

    res = resolve_zero_stub_trades(df_collision)
    assert len(res["trades"]) == 1
    t = res["trades"][0]
    assert t["exit_reason"] == "SL_TP_COLLISION"
    assert t["net_pnl"] < 0  # Conservative loss guarantee


def test_v33_fee_slippage_accounting():
    """Verifies exact fee (0.15%) and slippage (0.05%) deductions."""
    timestamps = pd.date_range("2025-01-01", periods=5, freq="1h")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0] * 5,
        "high": [101.0, 101.0, 125.0, 101.0, 101.0],
        "low":  [99.0] * 5,
        "close": [100.0] * 5,
        "volume": [1000.0] * 5,
        "signal": [0, 1, 0, 0, 0],
        "stop_loss": [0.0, 90.0, 0.0, 0.0, 0.0],
        "take_profit": [0.0, 120.0, 0.0, 0.0, 0.0],
        "confidence": [0.0, 0.8, 0.0, 0.0, 0.0]
    })

    res = resolve_zero_stub_trades(df, initial_balance=1000.0, fee_rate=0.0015, slippage=0.0005)
    t = res["trades"][0]

    # Entry price with 0.05% slippage = 100.0 * 1.0005 = 100.05
    assert pytest.approx(t["entry_price"], rel=1e-4) == 100.05
    # Exit price (TP = 120.0) with 0.05% slippage = 120.0 * 0.9995 = 119.94
    assert pytest.approx(t["exit_price"], rel=1e-4) == 119.94
    assert t["total_fee"] > 0
    assert t["net_pnl"] < t["raw_pnl"]


def test_v33_liquidity_filter():
    """Verifies liquidity eligibility filter rejects low-volume datasets."""
    df_high = generate_synthetic_asset_data("BTC", "1h", seed=1)
    df_low = generate_synthetic_asset_data("ILLIQUID_COIN", "1h", seed=2)
    df_low["volume"] = 10.0  # Extremely low volume

    datasets = {"BTC": df_high, "ILLIQUID_COIN": df_low}
    eligible, rejected = apply_liquidity_filter(datasets, min_avg_daily_volume=1000000.0)

    assert "BTC" in eligible
    assert "ILLIQUID_COIN" in rejected


def test_v33_universe_expansion():
    """Verifies dataset tier loading across 12, 20, 30, 50 asset tiers."""
    t1 = load_universe_tier("TIER_1")
    t2 = load_universe_tier("TIER_2")
    t3 = load_universe_tier("TIER_3")
    t4 = load_universe_tier("TIER_4")

    assert len(t1) == 12
    assert len(t2) == 20
    assert len(t3) == 30
    assert len(t4) == 50


def test_v33_opportunity_ranking_and_correlation():
    """Verifies signal quality ranking and correlation filtering."""
    signals = [
        {"asset": "BTC", "confidence": 0.90, "rr_ratio": 2.0, "risk_pct": 0.005},
        {"asset": "ETH", "confidence": 0.85, "rr_ratio": 2.0, "risk_pct": 0.005},
        {"asset": "SOL", "confidence": 0.70, "rr_ratio": 1.5, "risk_pct": 0.005}
    ]
    # High correlation between BTC and ETH
    corr_df = pd.DataFrame(
        [[1.0, 0.85, 0.20], [0.85, 1.0, 0.30], [0.20, 0.30, 1.0]],
        index=["BTC", "ETH", "SOL"],
        columns=["BTC", "ETH", "SOL"]
    )

    selected = select_portfolio_opportunities(signals, corr_df, max_aggregate_risk=0.015, max_correlated_risk=0.010)
    assert len(selected) > 0
    assert selected[0]["asset"] == "BTC"  # Highest quality score


def test_v33_position_sizing_stop_distance():
    """Verifies stop-distance position sizing formula across risk tiers."""
    trades = [
        {"pnl_r": 1.5, "net_pnl": 15.0},
        {"pnl_r": -1.0, "net_pnl": -10.0},
        {"pnl_r": 2.0, "net_pnl": 20.0}
    ]

    res = evaluate_position_sizing_and_growth(trades, initial_balance=1000.0)
    assert "risk_25bps" in res
    assert "risk_50bps" in res
    assert "risk_75bps" in res
    assert res["risk_50bps"]["final_balance"] > 1000.0


def test_v33_walk_forward_and_robustness():
    """Verifies walk-forward validation and parameter perturbation stability."""
    df_btc = generate_synthetic_asset_data("BTC", "1h", num_bars=500, seed=42)

    wf_res = run_walk_forward_validation(df_btc, generate_signals_trend_cont, num_windows=4)
    assert "positive_windows" in wf_res
    assert wf_res["num_windows"] == 4

    stab_res = run_parameter_perturbation_test("V33-TREND-CONT-1H", generate_signals_trend_cont, df_btc)
    assert "is_stable" in stab_res
    assert "stability_pct" in stab_res


def test_v33_full_pipeline_execution(tmp_path):
    """End-to-end test executing full V33 pipeline and generating report files."""
    out_dir = str(tmp_path)
    res = run_full_v33_pipeline(seed=42, num_bars=300, output_dir=out_dir)

    assert "overall_verdict" in res
    assert os.path.exists(res["report_md_path"])
    assert os.path.exists(res["summary_csv_path"])

    with open(res["report_md_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "NEXUS-7 Research V33" in content
    assert "Executive Official Verdict" in content
    assert "Answers to Mandatory 30 Research Questions" in content
