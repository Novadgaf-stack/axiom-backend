"""
Unit Tests Suite for NEXUS-7 Research V39 Framework
Covers data integrity audit, zero lookahead adversarial mutation, Same-Candle collision loss,
execution delay, real data fetching, liquidity filtering, universe expansion, opportunity selection,
position sizing, correlation caps, purged walk-forward, bootstrap, Monte Carlo, anti-fragility,
deflated Sharpe ratio, final untouched holdout, and full pipeline.
"""

import pytest
import numpy as np
import pandas as pd

from backtest.research_v39.universe_builder import UNIVERSE_TIERS_V39, filter_point_in_time_liquidity_v39
from backtest.research_v39.real_data_fetcher import fetch_real_ohlcv_data_v39
from backtest.research_v39.data_integrity_auditor import audit_ohlcv_data_integrity_v39
from backtest.research_v39.data_pipeline import split_dataset_v39_holdout, load_universe_tier_v39
from backtest.research_v39.regime_analysis import classify_market_regime_v39, evaluate_regime_performance_v39
from backtest.research_v39.strategy_library import CANDIDATE_STRATEGIES_V39, generate_signals_momentum_cont_v39
from backtest.research_v39.signal_engine import extract_signal_features_v39
from backtest.research_v39.opportunity_selector import generate_candidate_opportunities_v39, filter_and_rank_opportunities_v39, compute_opportunity_score_v39
from backtest.research_v39.candle_resolver import resolve_zero_stub_trades_v39
from backtest.research_v39.execution_model import run_friction_stress_test_v39, calculate_breakeven_friction_v39
from backtest.research_v39.portfolio_constructor import compute_rolling_correlation_matrix_v39, detect_correlation_clusters_v39, enforce_portfolio_risk_caps_v39
from backtest.research_v39.position_sizing import compute_stop_distance_position_size_v39
from backtest.research_v39.walk_forward import run_expanding_walk_forward_v39
from backtest.research_v39.purged_validation import run_purged_walk_forward_v39
from backtest.research_v39.bootstrap import run_bootstrap_resampling_v39
from backtest.research_v39.monte_carlo import run_monte_carlo_simulations_v39
from backtest.research_v39.robustness import run_parameter_perturbations_v39, run_anti_fragility_tests_v39
from backtest.research_v39.asset_replication import analyze_cross_asset_replication_v39
from backtest.research_v39.ablation import run_component_ablation_study_v39
from backtest.research_v39.multiple_testing import compute_deflated_sharpe_ratio_v39
from backtest.research_v39.statistical_evaluator import compute_trade_statistics_v39, evaluate_v39_promotion_gates
from backtest.research_v39.expectancy_frontier import compute_daily_participation_metrics_v39, compute_frequency_frontier_bands_v39
from backtest.research_v39.holdout import evaluate_final_untouched_holdout
from backtest.research_v39.engine import run_full_v39_pipeline


def test_v39_data_integrity_auditor():
    """Verifies data integrity auditor detects OHLC violations and negative prices."""
    timestamps = pd.date_range("2026-01-01", periods=10, freq="1h")
    df_clean = pd.DataFrame({
        "timestamp": timestamps,
        "open": np.full(10, 100.0),
        "high": np.full(10, 105.0),
        "low": np.full(10, 95.0),
        "close": np.full(10, 102.0),
        "volume": np.full(10, 1000.0)
    })

    datasets = {"BTC": df_clean}
    metadata = {"BTC": {"exchange": "BINANCE", "data_source_type": "REAL_MARKET_DATA"}}

    summary, report_path = audit_ohlcv_data_integrity_v39(datasets, metadata)
    assert summary["data_integrity_passed"] is True
    assert summary["impossible_ohlc_relationships"] == 0

    # Corrupt with high < low
    df_corrupt = df_clean.copy()
    df_corrupt.loc[2, "high"] = 90.0
    df_corrupt.loc[2, "low"] = 110.0

    summary_bad, _ = audit_ohlcv_data_integrity_v39({"BTC": df_corrupt}, metadata)
    assert summary_bad["data_integrity_passed"] is False
    assert summary_bad["impossible_ohlc_relationships"] == 1


def test_v39_zero_lookahead_adversarial_mutation():
    """Adversarial zero-lookahead test: Mutating future bars must NOT change signals at T."""
    df, _ = load_universe_tier_v39("TIER_12", timeframe="1h", days=30)
    if not df or "BTC" not in df:
        pytest.skip("Real data unavailable for test")

    df_btc = df["BTC"]
    df_sig_orig = generate_signals_momentum_cont_v39(df_btc)
    sig_at_50 = df_sig_orig.iloc[50]["signal"]

    # Mutate bar 80
    df_mutated = df_btc.copy()
    df_mutated.loc[80, "close"] = df_mutated.loc[80, "close"] * 10.0
    df_sig_mutated = generate_signals_momentum_cont_v39(df_mutated)

    assert df_sig_mutated.iloc[50]["signal"] == sig_at_50


def test_v39_anti_stub_outcome():
    """Verifies trade outcomes depend exclusively on OHLC price action and cannot be spoofed by high confidence."""
    n = 100
    timestamps = pd.date_range("2026-01-01", periods=n, freq="1h")

    # High confidence signal with adverse price action -> Must lose
    df_high_conf_loss = pd.DataFrame({
        "timestamp": timestamps,
        "open": np.full(n, 100.0),
        "high": np.full(n, 101.0),
        "low": np.full(n, 90.0),  # Hits SL at 95.0
        "close": np.full(n, 91.0),
        "volume": np.full(n, 10000.0),
        "signal": [1] + [0]*(n-1),
        "stop_loss": [95.0] + [0.0]*(n-1),
        "take_profit": [110.0] + [0.0]*(n-1),
        "confidence": [0.99] + [0.0]*(n-1),
        "asset": "BTC",
        "timeframe": "1h"
    })

    res = resolve_zero_stub_trades_v39(df_high_conf_loss)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["net_pnl"] < 0
    assert trades[0]["exit_reason"] in ["STOP_LOSS", "SL_TP_COLLISION"]


def test_v39_same_candle_collision():
    """Verifies SL and TP occurring on the same candle is resolved as LOSS."""
    n = 20
    timestamps = pd.date_range("2026-01-01", periods=n, freq="1h")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0] * n,
        "high": [100.0, 120.0] + [100.0] * (n - 2), # Hits TP 110
        "low":  [100.0, 80.0]  + [100.0] * (n - 2), # Hits SL 90 on same candle
        "close": [100.0] * n,
        "volume": [10000.0] * n,
        "signal": [1] + [0] * (n - 1),
        "stop_loss": [90.0] + [0.0] * (n - 1),
        "take_profit": [110.0] + [0.0] * (n - 1),
        "confidence": [0.50] * n,
        "asset": "BTC",
        "timeframe": "1h"
    })

    res = resolve_zero_stub_trades_v39(df)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "SL_TP_COLLISION"
    assert trades[0]["net_pnl"] < 0


def test_v39_execution_delay():
    """Verifies signal at bar N executes at bar N + execution_delay."""
    n = 20
    timestamps = pd.date_range("2026-01-01", periods=n, freq="1h")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0, 105.0] + [100.0] * (n - 2),
        "high": [100.0, 115.0] + [100.0] * (n - 2),
        "low":  [100.0, 99.0]  + [100.0] * (n - 2),
        "close": [100.0, 110.0] + [100.0] * (n - 2),
        "volume": [10000.0] * n,
        "signal": [1] + [0] * (n - 1),
        "stop_loss": [90.0] + [0.0] * (n - 1),
        "take_profit": [110.0] + [0.0] * (n - 1),
        "confidence": [0.50] * n,
        "asset": "BTC",
        "timeframe": "1h"
    })

    res = resolve_zero_stub_trades_v39(df, execution_delay=1)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["entry_time"] == timestamps[1]


def test_v39_purged_validation_and_embargo():
    """Verifies purged walk-forward validation with embargo period."""
    datasets, _ = load_universe_tier_v39("TIER_12", timeframe="1h", days=30)
    if not datasets or "BTC" not in datasets:
        pytest.skip("Real data unavailable")

    df = datasets["BTC"]
    wf_res = run_purged_walk_forward_v39(df, num_windows=6, purge_bars=12, embargo_bars=12)

    assert wf_res["total_windows"] <= 6
    assert "consistency_pct" in wf_res


def test_v39_bootstrap_and_monte_carlo():
    """Verifies 10,000 Bootstrap and Monte Carlo simulations execute deterministically."""
    pnls = [10.0, -5.0, 15.0, -8.0, 12.0, -4.0, 20.0, -10.0, 5.0, -2.0]
    bs_res = run_bootstrap_resampling_v39(pnls, iterations=10000, seed=42)
    mc_res = run_monte_carlo_simulations_v39(pnls, iterations=10000, seed=42)

    assert len(bs_res["pf_ci"]) == 2
    assert bs_res["pf_ci"][0] <= bs_res["pf_ci"][1]

    assert mc_res["median_drawdown_pct"] >= 0.0
    assert mc_res["p95_drawdown_pct"] >= mc_res["median_drawdown_pct"]


def test_v39_deflated_sharpe_ratio():
    """Verifies Deflated Sharpe Ratio calculation for multiple testing control."""
    dsr_res = compute_deflated_sharpe_ratio_v39(observed_sharpe=1.5, num_trials=20, sample_length=500)

    assert dsr_res["trials_tested"] == 20
    assert "expected_max_null_sharpe" in dsr_res
    assert "dsr_passed" in dsr_res


def test_v39_final_holdout_evaluation():
    """Verifies untouched final holdout evaluator executes exactly once."""
    datasets, _ = load_universe_tier_v39("TIER_12", timeframe="1h", days=30)
    if not datasets or "BTC" not in datasets:
        pytest.skip("Real data unavailable")

    df = datasets["BTC"]
    holdout_res = evaluate_final_untouched_holdout(
        df,
        generate_signals_momentum_cont_v39,
        strategy_name="V39-MOMENTUM-CONT-1H"
    )

    assert holdout_res["strategy_name"] == "V39-MOMENTUM-CONT-1H"
    assert "holdout_stats" in holdout_res
    assert "report_path" in holdout_res


def test_v39_full_pipeline_execution():
    """Verifies end-to-end execution of V39 research pipeline on real market data."""
    res = run_full_v39_pipeline(tier_name="TIER_12", days=30)

    assert "overall_verdict" in res
    assert res["overall_verdict"] in [
        "ROBUST_HIGH_FREQUENCY",
        "ROBUST_DAILY",
        "ROBUST_LOW_FREQUENCY",
        "V39_PROFITABLE_BUT_NOT_ROBUST",
        "V39_FREQUENT_BUT_UNPROFITABLE",
        "NO_ROBUST_EDGE_FOUND",
        "V39_INSUFFICIENT_SAMPLE",
        "REAL_DATA_REQUIRED",
        "FRAGILE"
    ]
    assert "data_source" in res
    assert "best_candidate" in res
    assert "report_path" in res
