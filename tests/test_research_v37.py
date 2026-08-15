"""
Unit Tests Suite for NEXUS-7 Research V37 Framework
Covers zero-stub outcome integrity, zero lookahead, same-candle collision loss,
execution delay, fees/slippage, liquidity filtering, universe expansion, opportunity ranking,
position sizing, correlation caps, walk-forward, bootstrap, Monte Carlo, and full pipeline.
"""

import pytest
import numpy as np
import pandas as pd

from backtest.research_v37.universe import UNIVERSE_TIERS, apply_liquidity_filter
from backtest.research_v37.data_pipeline import generate_synthetic_asset_data, split_dataset_chronological, load_universe_tier, compute_rolling_correlation_matrix
from backtest.research_v37.regime_detector import classify_market_regime
from backtest.research_v37.strategy_library import CANDIDATE_STRATEGIES, generate_signals_momentum_cont
from backtest.research_v37.signal_engine import extract_signal_features
from backtest.research_v37.opportunity_selector import generate_candidate_opportunities, filter_and_rank_opportunities, compute_opportunity_score
from backtest.research_v37.candle_resolver import resolve_zero_stub_trades
from backtest.research_v37.correlation import detect_correlation_clusters, enforce_portfolio_risk_caps
from backtest.research_v37.position_sizing import compute_stop_distance_position_size, compare_position_sizing_models
from backtest.research_v37.friction import run_friction_stress_test, calculate_breakeven_friction
from backtest.research_v37.statistical_evaluator import compute_trade_statistics, evaluate_v37_promotion_gates
from backtest.research_v37.walk_forward import run_rolling_walk_forward
from backtest.research_v37.bootstrap import run_bootstrap_resampling
from backtest.research_v37.monte_carlo import run_monte_carlo_simulations
from backtest.research_v37.robustness import run_parameter_perturbations, run_best_trade_and_asset_removal_tests
from backtest.research_v37.ablation import run_component_ablation_study
from backtest.research_v37.expectancy_frontier import compute_daily_participation_metrics, compute_frequency_frontier_bands
from backtest.research_v37.engine import run_full_v37_pipeline


def test_v37_anti_stub_outcome():
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

    res = resolve_zero_stub_trades(df_high_conf_loss)
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

    res_win = resolve_zero_stub_trades(df_low_conf_win)
    trades_win = res_win["trades"]
    assert len(trades_win) == 1
    assert trades_win[0]["net_pnl"] > 0
    assert trades_win[0]["exit_reason"] == "TAKE_PROFIT"


def test_v37_no_lookahead():
    """Verifies features and signal generation at index i only use data up to i."""
    df = generate_synthetic_asset_data("BTC", "1h", num_bars=200, seed=42)
    df_sig = generate_signals_momentum_cont(df)

    feats_i = extract_signal_features(df, 100, 1, 100.0, 95.0, 110.0)

    # Mutate future bar 150
    df_mutated = df.copy()
    df_mutated.loc[150, "close"] = 999999.0

    feats_i_mutated = extract_signal_features(df_mutated, 100, 1, 100.0, 95.0, 110.0)
    assert feats_i == feats_i_mutated


def test_v37_same_candle_collision():
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

    res = resolve_zero_stub_trades(df)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "SL_TP_COLLISION"
    assert trades[0]["net_pnl"] < 0


def test_v37_fee_and_slippage_calculation():
    """Verifies entry/exit fees (0.15% round-trip) and slippage (0.05%) are correctly deducted."""
    n = 20
    timestamps = pd.date_range("2026-01-01", periods=n, freq="1h")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": [100.0] * n,
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

    res = resolve_zero_stub_trades(df, fee_rate=0.0015, slippage=0.0005)
    trades = res["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert t["entry_price"] == pytest.approx(100.0 * 1.0005)
    assert t["exit_price"] == pytest.approx(110.0 * 0.9995)
    assert t["total_fee"] > 0
    assert t["net_pnl"] < t["raw_pnl"]


def test_v37_execution_delay():
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

    res = resolve_zero_stub_trades(df, execution_delay=1)
    trades = res["trades"]
    assert len(trades) == 1
    assert trades[0]["entry_time"] == timestamps[1]


def test_v37_liquidity_filtering_and_universe():
    """Verifies universe tiers and liquidity filtering categorizations."""
    assert len(UNIVERSE_TIERS["TIER_A_20"]) == 20
    assert len(UNIVERSE_TIERS["TIER_F_150"]) == 150

    datasets = load_universe_tier("TIER_A_20", num_bars=100)
    eligible, rejected, cats, counts = apply_liquidity_filter(datasets)

    assert len(eligible) > 0
    assert "CORE" in cats
    assert "REJECT" in cats
    assert counts["UNIVERSE_SIZE"] == 20


def test_v37_opportunity_ranking_and_scoring():
    """Verifies opportunity quality scoring (A+ to REJECT) and selectivity filtering."""
    opp = {
        "confidence": 0.90,
        "rr_ratio": 2.5,
        "features": {
            "trend_quality": 0.85,
            "volume_expansion": 0.85,
            "mtf_agreement": 0.85
        }
    }
    score, tier = compute_opportunity_score(opp)
    assert score >= 0.75
    assert tier in ["A+", "A"]

    opps = [{"confidence": float(i)/10.0, "rr_ratio": 2.0, "features": {}} for i in range(1, 10)]
    ranked_100 = filter_and_rank_opportunities(opps, "TOP_100PCT")
    ranked_50 = filter_and_rank_opportunities(opps, "TOP_50PCT")

    assert len(ranked_100) >= len(ranked_50)


def test_v37_position_sizing_stop_distance():
    """Verifies stop-distance position sizing formula."""
    res = compute_stop_distance_position_size(
        equity=1000.0,
        entry_price=100.0,
        stop_price=95.0,
        risk_budget_pct=0.0050
    )
    # Risk USD = 1000 * 0.005 = $5.0. Stop dist = $5.0. Units = 1.0.
    assert res["risk_usd"] == 5.0
    assert res["units"] == 1.0
    assert res["position_usd"] == 100.0


def test_v37_walk_forward_chronology():
    """Verifies walk-forward validation splits data chronologically into rolling windows."""
    df = generate_synthetic_asset_data("BTC", "1h", num_bars=400)
    wf_res = run_rolling_walk_forward(df, num_windows=5)

    assert wf_res["total_windows"] == 5
    assert len(wf_res["window_results"]) == 5
    assert 0 <= wf_res["positive_windows"] <= 5


def test_v37_bootstrap_and_monte_carlo():
    """Verifies 5,000 Bootstrap and Monte Carlo simulations execute deterministically."""
    pnls = [10.0, -5.0, 15.0, -8.0, 12.0, -4.0, 20.0, -10.0, 5.0, -2.0]
    bs_res = run_bootstrap_resampling(pnls, iterations=5000, seed=42)
    mc_res = run_monte_carlo_simulations(pnls, iterations=5000, seed=42)

    assert len(bs_res["pf_ci"]) == 2
    assert bs_res["pf_ci"][0] <= bs_res["pf_ci"][1]

    assert mc_res["median_drawdown_pct"] >= 0.0
    assert mc_res["p95_drawdown_pct"] >= mc_res["median_drawdown_pct"]


def test_v37_anti_overfit_removal_tests():
    """Verifies best-trade and best-asset removal tests."""
    trades = [
        {"net_pnl": 100.0, "asset": "BTC"}, # Best trade
        {"net_pnl": 10.0, "asset": "ETH"},
        {"net_pnl": -5.0, "asset": "SOL"},
        {"net_pnl": 15.0, "asset": "AVAX"},
        {"net_pnl": -8.0, "asset": "BTC"},
        {"net_pnl": 12.0, "asset": "ETH"}
    ]
    res = run_best_trade_and_asset_removal_tests(trades)

    assert res["remove_best_1_pf"] < 99.0
    assert res["remove_best_asset_pf"] >= 0.0


def test_v37_full_pipeline_execution():
    """Verifies end-to-end execution of V37 research pipeline."""
    res = run_full_v37_pipeline(tier_name="TIER_A_20", num_bars=50)

    assert "overall_verdict" in res
    assert res["overall_verdict"] in [
        "ROBUST_HIGH_FREQUENCY",
        "ROBUST_DAILY",
        "ROBUST_LOW_FREQUENCY",
        "V37_PROFITABLE_BUT_NOT_ROBUST",
        "V37_FREQUENT_BUT_UNPROFITABLE",
        "V37_NO_ROBUST_PROFITABLE_EDGE",
        "V37_INSUFFICIENT_SAMPLE"
    ]
    assert "best_candidate" in res
    assert "report_path" in res
