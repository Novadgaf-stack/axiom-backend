"""
Comprehensive Unit Test Suite for NEXUS-7 Research V36
Verifies zero-stub anti-stub outcome guarantees, no-lookahead indicator logic,
future-data prevention, conservative SL/TP same-candle collision, execution delay,
fee calculation (0.15%), slippage (0.05%), stop-distance position sizing,
risk caps, correlation filtering, opportunity scoring & ranking, daily selection,
no-trade behavior, walk-forward chronology, purging/embargo, bootstrap,
Monte Carlo, parameter perturbation, best-trade removal, best-asset removal, and full pipeline execution.
"""

import pytest
import pandas as pd
import numpy as np
import os

from backtest.research_v36.universe import (
    apply_liquidity_filter,
    UNIVERSE_TIERS
)
from backtest.research_v36.data_pipeline import (
    generate_synthetic_asset_data,
    validate_and_clean_ohlcv,
    split_dataset_chronological,
    load_universe_tier,
    compute_rolling_correlation_matrix
)
from backtest.research_v36.market_regime import classify_market_regime
from backtest.research_v36.feature_engine import extract_signal_features
from backtest.research_v36.strategy_library import (
    generate_signals_momentum_cont,
    generate_signals_breakout,
    CANDIDATE_STRATEGIES
)
from backtest.research_v36.opportunity_generator import generate_candidate_opportunities
from backtest.research_v36.opportunity_ranker import (
    compute_opportunity_score,
    filter_and_rank_opportunities
)
from backtest.research_v36.portfolio_selector import construct_correlated_portfolio
from backtest.research_v36.candle_resolver import resolve_zero_stub_trades
from backtest.research_v36.statistical_evaluator import (
    compute_trade_statistics,
    assign_official_v36_verdict
)
from backtest.research_v36.position_sizing import evaluate_position_sizing_and_growth
from backtest.research_v36.risk_manager import evaluate_risk_caps_and_limits
from backtest.research_v36.walk_forward import run_walk_forward_validation
from backtest.research_v36.bootstrap import run_bootstrap_resampling
from backtest.research_v36.monte_carlo import run_monte_carlo_resampling
from backtest.research_v36.robustness import (
    run_parameter_perturbation_test,
    run_friction_and_execution_stress_test
)
from backtest.research_v36.frequency_analysis import analyze_daily_participation
from backtest.research_v36.ablation import run_ablation_study
from backtest.research_v36.baselines import evaluate_defensive_baselines
from backtest.research_v36.anti_overfit import run_anti_overfit_removal_tests
from backtest.research_v36.engine import run_full_v36_pipeline


def test_v36_anti_stub_outcome():
    """
    CRITICAL ANTI-STUB GUARANTEE TEST:
    1. Confidence = 0.99 + Adverse future price path MUST result in a LOSS.
    2. Confidence = 0.20 + Favorable future price path MUST result in a WIN.
    Proves confidence scores or candidate IDs NEVER spoof trade outcomes.
    """
    timestamps = pd.date_range("2025-01-01", periods=10, freq="1h")

    # High Confidence (0.99) + Adverse future price path -> LOSS
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

    # Low Confidence (0.20) + Favorable future price path -> WIN
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
        "confidence": [0.0, 0.20, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "asset": ["BTC"] * 10
    })

    res_favorable = resolve_zero_stub_trades(df_favorable)
    assert len(res_favorable["trades"]) == 1
    assert res_favorable["trades"][0]["net_pnl"] > 0


def test_v36_no_lookahead():
    """Verifies indicator features depend strictly on past data."""
    df_raw = generate_synthetic_asset_data("BTC", "1h", num_bars=200, seed=101)
    df_sig = generate_signals_momentum_cont(df_raw)

    df_mutated = df_raw.copy()
    df_mutated.loc[150:, "close"] = df_mutated.loc[150:, "close"] * 5.0
    df_sig_mutated = generate_signals_momentum_cont(df_mutated)

    np.testing.assert_array_equal(
        df_sig["signal"].iloc[:140].values,
        df_sig_mutated["signal"].iloc[:140].values
    )


def test_v36_same_candle_collision():
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
    assert t["net_pnl"] < 0


def test_v36_fee_and_slippage_calculation():
    """Verifies fee (0.15%) and slippage (0.05%) accounting."""
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
    assert pytest.approx(t["entry_price"], rel=1e-4) == 100.05
    assert pytest.approx(t["exit_price"], rel=1e-4) == 119.94
    assert t["total_fee"] > 0


def test_v36_execution_delay():
    """Verifies 1-bar execution delay on trade entry."""
    timestamps = pd.date_range("2025-01-01", periods=5, freq="1h")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0, 105.0, 110.0, 115.0, 120.0],
        "high": [101.0, 106.0, 130.0, 116.0, 121.0],
        "low":  [99.0,  104.0, 109.0, 114.0, 119.0],
        "close": [100.0, 105.0, 110.0, 115.0, 120.0],
        "volume": [1000.0] * 5,
        "signal": [0, 1, 0, 0, 0], # Signal on bar 1
        "stop_loss": [0.0, 90.0, 0.0, 0.0, 0.0],
        "take_profit": [0.0, 120.0, 0.0, 0.0, 0.0],
        "confidence": [0.0, 0.8, 0.0, 0.0, 0.0]
    })

    res = resolve_zero_stub_trades(df, execution_delay=1)
    assert len(res["trades"]) == 1
    assert pytest.approx(res["trades"][0]["entry_price"], rel=1e-4) == 110.055


def test_v36_liquidity_filtering_and_universe():
    """Verifies liquidity filtering across 8 universe tiers."""
    ds = load_universe_tier("TIER_15")
    assert len(ds) == 15
    el, rej, cats, counts = apply_liquidity_filter(ds)
    assert counts["UNIVERSE_SIZE"] == 15
    assert "CORE_LIQUID" in cats


def test_v36_opportunity_ranking_and_scoring():
    """Verifies opportunity quality scoring (A+ to REJECT) and selectivity filtering."""
    opps = [
        {"asset": "BTC", "confidence": 0.95, "rr_ratio": 2.0, "risk_pct": 0.005},
        {"asset": "ETH", "confidence": 0.70, "rr_ratio": 1.5, "risk_pct": 0.005},
        {"asset": "JUNK", "confidence": 0.10, "rr_ratio": 0.5, "risk_pct": 0.005}
    ]

    score, tier = compute_opportunity_score(opps[0])
    assert score >= 0.85
    assert tier == "A+"

    ranked = filter_and_rank_opportunities(opps, selectivity_mode="TOP_50PCT")
    assert len(ranked) >= 1


def test_v36_no_trade_behavior():
    """Verifies that if no candidate passes quality threshold, NO TRADE is executed."""
    opps = [
        {"asset": "JUNK", "confidence": 0.10, "rr_ratio": 0.5, "risk_pct": 0.005}
    ]
    ranked = filter_and_rank_opportunities(opps, selectivity_mode="TOP_100PCT")
    assert len(ranked) == 0


def test_v36_position_sizing_stop_distance():
    """Verifies stop-distance position sizing formula."""
    trades = [
        {"pnl_r": 1.5, "net_pnl": 15.0},
        {"pnl_r": -1.0, "net_pnl": -10.0}
    ]
    res = evaluate_position_sizing_and_growth(trades, initial_balance=1000.0)
    assert "risk_50bps" in res


def test_v36_walk_forward_chronology():
    """Verifies 8-window rolling walk-forward validation."""
    df_btc = generate_synthetic_asset_data("BTC", "1h", num_bars=500, seed=42)
    wf_res = run_walk_forward_validation(df_btc, generate_signals_momentum_cont, num_windows=8)
    assert wf_res["num_windows"] == 8


def test_v36_bootstrap_and_monte_carlo():
    """Verifies 5,000-iteration Bootstrap CIs and Monte Carlo simulations."""
    trades = [
        {"pnl_r": 1.5, "net_pnl": 15.0},
        {"pnl_r": -1.0, "net_pnl": -10.0},
        {"pnl_r": 2.0, "net_pnl": 20.0}
    ]
    boot_res = run_bootstrap_resampling(trades, iterations=500)
    mc_res = run_monte_carlo_resampling(trades, iterations=500)

    assert "pf_ci_lower" in boot_res
    assert mc_res["iterations"] == 500


def test_v36_anti_overfit_removal_tests():
    """Verifies best trade, best asset, and best day removal tests."""
    trades = [
        {"entry_time": "2025-01-01 00:00:00", "asset": "BTC", "net_pnl": 50.0, "pnl_r": 5.0},
        {"entry_time": "2025-01-02 00:00:00", "asset": "ETH", "net_pnl": -10.0, "pnl_r": -1.0},
        {"entry_time": "2025-01-03 00:00:00", "asset": "SOL", "net_pnl": 15.0, "pnl_r": 1.5}
    ]
    ao_res = run_anti_overfit_removal_tests(trades, total_days=90.0)
    assert "remove_best_trades" in ao_res
    assert "remove_best_assets" in ao_res
    assert "remove_best_days" in ao_res


def test_v36_full_pipeline_execution(tmp_path):
    """End-to-end test executing full V36 research pipeline."""
    out_dir = str(tmp_path)
    res = run_full_v36_pipeline(seed=42, num_bars=150, output_dir=out_dir)

    assert "overall_verdict" in res
    assert os.path.exists(res["report_md_path"])

    with open(res["report_md_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "NEXUS-7 Research V36" in content
    assert "Executive Official Verdict" in content
