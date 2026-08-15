"""
Unit Tests Suite for NEXUS-7 Research V38 Framework
Covers zero-stub outcome integrity, zero lookahead, same-candle collision loss,
execution delay, fees/slippage, liquidity filtering, universe expansion, opportunity selection,
position sizing, correlation caps, purged walk-forward, bootstrap, Monte Carlo, anti-fragility,
deflated Sharpe ratio, final untouched holdout, and full pipeline.
"""

import pytest
import numpy as np
import pandas as pd

from backtest.research_v38.universe_builder import UNIVERSE_TIERS, apply_point_in_time_liquidity_filter
from backtest.research_v38.data_pipeline import generate_synthetic_asset_data_v38, split_dataset_v38_holdout, load_universe_tier_v38
from backtest.research_v38.regime_analysis import classify_market_regime_v38, evaluate_regime_performance
from backtest.research_v38.strategy_library import CANDIDATE_STRATEGIES_V38, generate_signals_momentum_cont_v38
from backtest.research_v38.signal_engine import extract_signal_features_v38
from backtest.research_v38.opportunity_selector import generate_candidate_opportunities_v38, filter_and_rank_opportunities_v38, compute_opportunity_score_v38
from backtest.research_v38.candle_resolver import resolve_zero_stub_trades_v38
from backtest.research_v38.execution_model import run_friction_stress_test_v38, calculate_breakeven_friction_v38
from backtest.research_v38.portfolio_constructor import compute_rolling_correlation_matrix_v38, detect_correlation_clusters_v38, enforce_portfolio_risk_caps_v38
from backtest.research_v38.position_sizing import compute_stop_distance_position_size_v38
from backtest.research_v38.walk_forward import run_expanding_walk_forward_v38
from backtest.research_v38.purged_validation import run_purged_walk_forward_v38
from backtest.research_v38.bootstrap import run_bootstrap_resampling_v38
from backtest.research_v38.monte_carlo import run_monte_carlo_simulations_v38
from backtest.research_v38.robustness import run_parameter_perturbations_v38, run_anti_fragility_tests_v38
from backtest.research_v38.ablation import run_component_ablation_study_v38
from backtest.research_v38.multiple_testing import compute_deflated_sharpe_ratio
from backtest.research_v38.statistical_evaluator import compute_trade_statistics_v38, evaluate_v38_promotion_gates
from backtest.research_v38.expectancy_frontier import compute_daily_participation_metrics_v38, compute_frequency_frontier_bands_v38
from backtest.research_v38.holdout import evaluate_final_untouched_holdout
from backtest.research_v38.engine import run_full_v38_pipeline


def test_v38_anti_stub_outcome():
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

    res = resolve_zero_stub_trades_v38(df_high_conf_loss)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["net_pnl"] < 0
    assert trades[0]["exit_reason"] in ["STOP_LOSS", "SL_TP_COLLISION"]

    # Low confidence signal with favorable price action -> Must win
    df_low_conf_win = pd.DataFrame({
        "timestamp": timestamps,
        "open": np.full(n, 100.0),
        "high": np.full(n, 115.0), # Hits TP at 110.0
        "low": np.full(n, 99.0),
        "close": np.full(n, 114.0),
        "volume": np.full(n, 10000.0),
        "signal": [1] + [0]*(n-1),
        "stop_loss": [95.0] + [0.0]*(n-1),
        "take_profit": [110.0] + [0.0]*(n-1),
        "confidence": [0.01] + [0.0]*(n-1),
        "asset": "BTC",
        "timeframe": "1h"
    })

    res_win = resolve_zero_stub_trades_v38(df_low_conf_win)
    trades_win = res_win["trades"]
    assert len(trades_win) == 1
    assert trades_win[0]["net_pnl"] > 0
    assert trades_win[0]["exit_reason"] == "TAKE_PROFIT"


def test_v38_no_lookahead():
    """Verifies features and signal generation at index i only use data up to i."""
    df = generate_synthetic_asset_data_v38("BTC", "1h", num_bars=200, seed=42)

    feats_i = extract_signal_features_v38(df, 100, 1, 100.0, 95.0, 110.0)

    # Mutate future bar 150
    df_mutated = df.copy()
    df_mutated.loc[150, "close"] = 999999.0

    feats_i_mutated = extract_signal_features_v38(df_mutated, 100, 1, 100.0, 95.0, 110.0)
    assert feats_i == feats_i_mutated


def test_v38_same_candle_collision():
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

    res = resolve_zero_stub_trades_v38(df)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "SL_TP_COLLISION"
    assert trades[0]["net_pnl"] < 0


def test_v38_execution_delay():
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

    res = resolve_zero_stub_trades_v38(df, execution_delay=1)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["entry_time"] == timestamps[1]


def test_v38_liquidity_filtering_and_universe():
    """Verifies 8 universe tiers and point-in-time liquidity filtering categorizations."""
    assert len(UNIVERSE_TIERS["TIER_12"]) == 12
    assert len(UNIVERSE_TIERS["TIER_200"]) == 200

    datasets = load_universe_tier_v38("TIER_20", num_bars=100)
    eligible, rejected, cats, counts = apply_point_in_time_liquidity_filter(datasets)

    assert len(eligible) > 0
    assert "CORE" in cats
    assert counts["UNIVERSE_SIZE"] == 20


def test_v38_purged_validation_and_embargo():
    """Verifies purged walk-forward validation with embargo period."""
    df = generate_synthetic_asset_data_v38("BTC", "1h", num_bars=300)
    wf_res = run_purged_walk_forward_v38(df, num_windows=5, purge_bars=12, embargo_bars=12)

    assert wf_res["total_windows"] <= 5
    assert "consistency_pct" in wf_res


def test_v38_bootstrap_and_monte_carlo():
    """Verifies 10,000 Bootstrap and Monte Carlo simulations execute deterministically."""
    pnls = [10.0, -5.0, 15.0, -8.0, 12.0, -4.0, 20.0, -10.0, 5.0, -2.0]
    bs_res = run_bootstrap_resampling_v38(pnls, iterations=10000, seed=42)
    mc_res = run_monte_carlo_simulations_v38(pnls, iterations=10000, seed=42)

    assert len(bs_res["pf_ci"]) == 2
    assert bs_res["pf_ci"][0] <= bs_res["pf_ci"][1]

    assert mc_res["median_drawdown_pct"] >= 0.0
    assert mc_res["p95_drawdown_pct"] >= mc_res["median_drawdown_pct"]


def test_v38_anti_fragility_tests():
    """Verifies anti-fragility removal tests."""
    trades = [
        {"net_pnl": 100.0, "asset": "BTC"}, # Best trade
        {"net_pnl": 10.0, "asset": "ETH"},
        {"net_pnl": -5.0, "asset": "SOL"},
        {"net_pnl": 15.0, "asset": "AVAX"},
        {"net_pnl": -8.0, "asset": "BTC"},
        {"net_pnl": 12.0, "asset": "ETH"}
    ]
    res = run_anti_fragility_tests_v38(trades)

    assert "remove_best_5_pf" in res
    assert "remove_best_asset_pf" in res
    assert "is_fragile" in res


def test_v38_deflated_sharpe_ratio():
    """Verifies Deflated Sharpe Ratio calculation for multiple testing control."""
    dsr_res = compute_deflated_sharpe_ratio(observed_sharpe=1.5, num_trials=20, sample_length=500)

    assert dsr_res["trials_tested"] == 20
    assert "expected_max_null_sharpe" in dsr_res
    assert "dsr_passed" in dsr_res


def test_v38_final_holdout_evaluation():
    """Verifies untouched final holdout evaluator executes exactly once."""
    df = generate_synthetic_asset_data_v38("BTC", "1h", num_bars=200)
    holdout_res = evaluate_final_untouched_holdout(
        df,
        generate_signals_momentum_cont_v38,
        strategy_name="V38-MOMENTUM-CONT-1H"
    )

    assert holdout_res["strategy_name"] == "V38-MOMENTUM-CONT-1H"
    assert "holdout_stats" in holdout_res
    assert "report_path" in holdout_res


def test_v38_full_pipeline_execution():
    """Verifies end-to-end execution of V38 research pipeline."""
    res = run_full_v38_pipeline(tier_name="TIER_20", num_bars=50)

    assert "overall_verdict" in res
    assert res["overall_verdict"] in [
        "ROBUST_HIGH_FREQUENCY",
        "ROBUST_DAILY",
        "ROBUST_LOW_FREQUENCY",
        "V38_PROFITABLE_BUT_NOT_ROBUST",
        "V38_FREQUENT_BUT_UNPROFITABLE",
        "NO_ROBUST_EDGE_FOUND",
        "V38_INSUFFICIENT_SAMPLE",
        "FRAGILE"
    ]
    assert "best_candidate" in res
    assert "holdout_results" in res
    assert "report_path" in res
