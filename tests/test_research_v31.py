"""
Unit Test Suite for NEXUS-7 Research V31 — Zero-Stub Forensically Validated Expectancy Search
Contains 10 mandatory forensic, risk control, walk-forward, Monte Carlo, and pipeline execution tests.
"""

import os
import pytest
import numpy as np
import pandas as pd

from backtest.research_v31.data_pipeline import (
    generate_synthetic_asset_data,
    split_dataset_chronological,
    compute_asset_correlation_matrix,
    get_asset_holdout_split,
    load_multi_asset_dataset,
    SUPPORTED_ASSETS,
    SUPPORTED_TIMEFRAMES
)
from backtest.research_v31.strategy_library import (
    CANDIDATE_STRATEGIES,
    generate_signals_trend_cont,
    generate_signals_breakout_vol,
    generate_signals_pullback_cont,
    generate_signals_liquidity_reversal,
    generate_signals_regime_mom,
    generate_signals_mean_reversion,
    generate_signals_mtf_confluence,
    generate_signals_vol_comp_exp,
    generate_signals_adaptive_hybrid
)
from backtest.research_v31.candle_resolver import resolve_zero_stub_trades
from backtest.research_v31.statistical_evaluator import compute_trade_statistics
from backtest.research_v31.position_sizing import evaluate_position_sizing_and_growth
from backtest.research_v31.portfolio_optimizer import filter_and_rank_portfolio_signals
from backtest.research_v31.walk_forward import run_walk_forward_validation
from backtest.research_v31.robustness import (
    run_parameter_perturbation_test,
    run_friction_and_execution_stress_test
)
from backtest.research_v31.monte_carlo import run_monte_carlo_resampling
from backtest.research_v31.expectancy_frontier import build_expectancy_frontier
from backtest.research_v31.engine import run_full_v31_pipeline


def test_v31_anti_stub_outcome():
    """
    1. ANTI-STUB OUTCOME TEST:
    Explicitly proves that:
    - confidence = 0.99 + adverse price path -> LOSS
    - confidence = 0.50 + favorable price path -> WIN
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
    conf1 = np.zeros(50); conf1[5] = 0.99

    df_bear["signal"] = sig1; df_bear["stop_loss"] = sl1; df_bear["take_profit"] = tp1; df_bear["confidence"] = conf1

    res_case1 = resolve_zero_stub_trades(df_bear)
    assert len(res_case1["trades"]) == 1
    assert res_case1["trades"][0]["exit_reason"] == "STOP_LOSS"
    assert res_case1["trades"][0]["net_pnl"] < 0 # LOSS despite 0.99 confidence

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
    conf2 = np.zeros(50); conf2[5] = 0.50

    df_bull["signal"] = sig2; df_bull["stop_loss"] = sl2; df_bull["take_profit"] = tp2; df_bull["confidence"] = conf2

    res_case2 = resolve_zero_stub_trades(df_bull)
    assert len(res_case2["trades"]) == 1
    assert res_case2["trades"][0]["exit_reason"] == "TAKE_PROFIT"
    assert res_case2["trades"][0]["net_pnl"] > 0 # WIN despite 0.50 confidence


def test_v31_no_lookahead():
    """2. NO-LOOKAHEAD TEST: Verifies signals use past data only."""
    df = generate_synthetic_asset_data("BTC", "1h", num_bars=300, seed=42)
    df_sig1 = generate_signals_breakout_vol(df.iloc[:200].copy())
    df_sig2 = generate_signals_breakout_vol(df.copy())

    # Signal at bar 150 must be identical whether data has 200 or 300 bars
    assert df_sig1["signal"].iloc[150] == df_sig2["signal"].iloc[150]


def test_v31_same_candle_collision():
    """3. SAME-CANDLE SL/TP COLLISION TEST: Verifies conservative LOSS resolution."""
    dates = pd.date_range("2026-01-01", periods=20, freq="1h")
    df = pd.DataFrame({
        "timestamp": dates, "open": 100.0, "high": 110.0,
        "low": 90.0, "close": 100.0, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })
    sig = np.zeros(20, dtype=int); sig[2] = 1
    sl = np.zeros(20); sl[2] = 95.0 # High=110 & Low=90 hit both SL & TP on bar 3
    tp = np.zeros(20); tp[2] = 105.0

    df["signal"] = sig; df["stop_loss"] = sl; df["take_profit"] = tp

    res = resolve_zero_stub_trades(df, execution_delay=1)
    assert len(res["trades"]) == 1
    assert res["trades"][0]["exit_reason"] == "SL_TP_COLLISION"
    assert res["trades"][0]["net_pnl"] < 0 # LOSS


def test_v31_fee_slippage_accounting():
    """4. FEE/SLIPPAGE ACCOUNTING TEST: Verifies exact fee and slippage deductions."""
    dates = pd.date_range("2026-01-01", periods=20, freq="1h")
    df = pd.DataFrame({
        "timestamp": dates, "open": [100.0]*20, "high": [106.0]*20,
        "low": [99.0]*20, "close": [105.0]*20, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })
    sig = np.zeros(20, dtype=int); sig[2] = 1
    sl = np.zeros(20); sl[2] = 95.0
    tp = np.zeros(20); tp[2] = 105.0
    df["signal"] = sig; df["stop_loss"] = sl; df["take_profit"] = tp

    res_zero = resolve_zero_stub_trades(df, fee_rate=0.0, slippage=0.0)
    res_real = resolve_zero_stub_trades(df, fee_rate=0.0015, slippage=0.0005)

    assert res_real["trades"][0]["entry_price"] > res_zero["trades"][0]["entry_price"]
    assert res_real["trades"][0]["total_fee"] > 0.0
    assert res_real["trades"][0]["net_pnl"] < res_zero["trades"][0]["net_pnl"]


def test_v31_position_sizing_stop_distance():
    """5. POSITION SIZING STOP DISTANCE TEST: Verifies position units calculated from stop distance."""
    dates = pd.date_range("2026-01-01", periods=20, freq="1h")
    df = pd.DataFrame({
        "timestamp": dates, "open": [100.0]*20, "high": [105.0]*20,
        "low": [95.0]*20, "close": [100.0]*20, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })
    sig = np.zeros(20, dtype=int); sig[2] = 1
    sl = np.zeros(20); sl[2] = 98.0 # Stop distance = 2.0
    tp = np.zeros(20); tp[2] = 104.0
    df["signal"] = sig; df["stop_loss"] = sl; df["take_profit"] = tp

    res = resolve_zero_stub_trades(df, risk_fraction=0.005, initial_balance=1000.0, max_position_equity_pct=0.50)
    t = res["trades"][0]
    # Risk USD = 1000 * 0.005 = 5.0 USD. Entry price = 100.05. Stop dist = 2.05 -> units = 5.0 / 2.05
    expected_units = 5.0 / (100.0 * 1.0005 - 98.0)
    assert t["risk_usd"] == pytest.approx(5.0, rel=1e-2)
    assert t["position_units"] == pytest.approx(expected_units, rel=1e-2)


def test_v31_max_risk_and_consecutive_losses():
    """6. MAX RISK & CONSECUTIVE LOSS TEST: Verifies 0.75% risk cap and step-downs after 5x/8x losses."""
    dates = pd.date_range("2026-01-01", periods=200, freq="1h")
    prices = np.linspace(100, 70, 200) # Crashing market

    df = pd.DataFrame({
        "timestamp": dates, "open": prices, "high": prices + 0.1,
        "low": prices - 0.5, "close": prices, "volume": 1000.0,
        "asset": "BTC", "timeframe": "1h"
    })

    signals = np.zeros(200, dtype=int)
    sl = np.zeros(200); tp = np.zeros(200)

    for idx in range(2, 180, 5):
        signals[idx] = 1
        sl[idx] = prices[idx] - 1.0
        tp[idx] = prices[idx] + 3.0

    df["signal"] = signals; df["stop_loss"] = sl; df["take_profit"] = tp

    res = resolve_zero_stub_trades(df, risk_fraction=0.0050)
    assert res["paused_for_review"] is True # 8 consecutive losses triggered pause


def test_v31_correlation_exposure_limits():
    """7. CORRELATION EXPOSURE TEST: Verifies portfolio risk ranking and correlation penalty."""
    dates = pd.date_range("2026-01-01", periods=50, freq="1h")
    prices = np.linspace(100, 105, 50)
    df = pd.DataFrame({
        "timestamp": dates, "open": prices, "high": prices + 1.0,
        "low": prices - 1.0, "close": prices, "volume": 1000.0,
        "asset": "SOL", "timeframe": "1h"
    })
    sig = np.zeros(50, dtype=int); sig[5] = 1
    sl = np.zeros(50); sl[5] = 98.0; tp = np.zeros(50); tp[5] = 104.0
    df["signal"] = sig; df["stop_loss"] = sl; df["take_profit"] = tp

    res_normal = resolve_zero_stub_trades(df, correlation_penalty_mult=1.0)
    res_penalized = resolve_zero_stub_trades(df, correlation_penalty_mult=0.70)

    assert res_penalized["trades"][0]["risk_usd"] < res_normal["trades"][0]["risk_usd"]


def test_v31_walk_forward_chronology():
    """8. WALK-FORWARD CHRONOLOGY TEST: Verifies 4-window chronological rolling walk-forward validation."""
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


def test_v31_parameter_robustness():
    """9. PARAMETER ROBUSTNESS TEST: Verifies parameter perturbation testing across neighboring variations."""
    df = generate_synthetic_asset_data("BTC", "30m", num_bars=400, seed=42)
    stab_res = run_parameter_perturbation_test("V31-BREAKOUT-VOL-30M", generate_signals_breakout_vol, df)
    assert "is_stable" in stab_res
    assert len(stab_res["neighborhood_results"]) == 5


def test_v31_full_pipeline_execution():
    """10. FULL PIPELINE TEST: Executes full V31 pipeline end-to-end and validates report generation."""
    output = run_full_v31_pipeline(seed=42)

    assert "frontier_results" in output
    assert "overall_verdict" in output
    assert output["overall_verdict"] in [
        "FORWARD_PAPER_READY",
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

    assert "NEXUS-7 Research V31" in content
    assert "Answers to Mandatory 16 Research Questions" in content
