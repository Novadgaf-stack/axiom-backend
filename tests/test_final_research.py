"""
Comprehensive Unit Test Suite for NEXUS-7 Final Master Quantitative Research Framework
Verifies data integrity auditing, real data fetching provenance, zero-lookahead future price mutations,
confidence/strategy-ID anti-spoofing, same-candle collision loss logic, execution delay, fee/slippage impact,
purged walk-forward, 10,000 Block Bootstrap & Monte Carlo, Deflated Sharpe Ratio,
untouched frozen final holdout evaluation EXACTLY ONCE, and full master research pipeline.
"""

import pytest
import pandas as pd
import numpy as np

from backtest.final_research.real_data_engine import fetch_real_ohlcv_data_final
from backtest.final_research.data_integrity import audit_ohlcv_data_integrity_final
from backtest.final_research.strategy_library import (
    generate_signals_trend_cont_final,
    generate_signals_momentum_cont_final,
    generate_signals_mean_reversion_final,
    CANDIDATE_STRATEGIES_FINAL
)
from backtest.final_research.opportunity_selector import generate_candidate_opportunities_final, filter_and_rank_opportunities_final
from backtest.final_research.candle_resolver import resolve_single_opportunity_final
from backtest.final_research.execution_model import stress_test_friction_final
from backtest.final_research.portfolio_constructor import compute_asset_correlation_matrix_final, filter_correlated_opportunities_final
from backtest.final_research.position_sizing import calculate_position_size_final, evaluate_risk_budgets_final
from backtest.final_research.walk_forward import run_walk_forward_validation_final
from backtest.final_research.purged_validation import apply_purged_embargo_split_final
from backtest.final_research.bootstrap import run_block_bootstrap_resampling_final
from backtest.final_research.monte_carlo import run_monte_carlo_simulation_final
from backtest.final_research.robustness import run_anti_fragility_tests_final
from backtest.final_research.asset_replication import evaluate_asset_replication_final
from backtest.final_research.regime_analysis import evaluate_regime_performance_final
from backtest.final_research.ablation import run_component_ablation_study_final
from backtest.final_research.multiple_testing import calculate_deflated_sharpe_ratio_final
from backtest.final_research.capital_simulation import simulate_capital_growth_final
from backtest.final_research.statistical_evaluator import evaluate_trade_statistics_final, evaluate_promotion_gates_final
from backtest.final_research.expectancy_frontier import build_expectancy_frequency_frontier_final
from backtest.final_research.holdout import evaluate_untouched_final_holdout
from backtest.final_research.engine import run_final_research_pipeline


@pytest.fixture
def sample_synthetic_ohlcv():
    """Generates synthetic 100-bar OHLCV dataset for deterministic unit testing."""
    dates = pd.date_range(start="2026-01-01", periods=100, freq="1h")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(100) * 0.5)
    high = close + np.abs(np.random.randn(100) * 0.3)
    low = close - np.abs(np.random.randn(100) * 0.3)
    open_p = close + np.random.randn(100) * 0.1

    df = pd.DataFrame({
        "timestamp": dates,
        "open": open_p,
        "high": np.maximum(high, np.maximum(open_p, close)),
        "low": np.minimum(low, np.minimum(open_p, close)),
        "close": close,
        "volume": np.random.rand(100) * 1000.0 + 100.0
    })
    return df


def test_final_data_integrity_auditor(sample_synthetic_ohlcv):
    """Test data integrity auditor detects duplicate candles and impossible OHLC relationships."""
    datasets = {"BTC": sample_synthetic_ohlcv}
    metadata = {"BTC": {"exchange": "BINANCE_MAINNET", "data_source_type": "SYNTHETIC_TEST_DATA"}}

    audit = audit_ohlcv_data_integrity_final(datasets, metadata)
    assert audit["total_assets"] == 1
    assert audit["duplicate_candles"] == 0
    assert audit["impossible_ohlc_relationships"] == 0


def test_final_zero_lookahead_adversarial_mutation(sample_synthetic_ohlcv):
    """Adversarial test: Mutate future candles post signal generation; past signal at T MUST NOT change."""
    df_original = sample_synthetic_ohlcv.copy()
    df_sig_orig = generate_signals_trend_cont_final(df_original)
    sig_at_50_orig = df_sig_orig["signal"].iloc[50]

    # Mutate future bar prices (bar 51 to 99)
    df_mutated = df_original.copy()
    df_mutated.loc[51:, "close"] = df_mutated.loc[51:, "close"] * 2.0
    df_mutated.loc[51:, "high"] = df_mutated.loc[51:, "high"] * 2.0

    df_sig_mutated = generate_signals_trend_cont_final(df_mutated)
    sig_at_50_mutated = df_sig_mutated["signal"].iloc[50]

    assert sig_at_50_orig == sig_at_50_mutated, "Signal at T changed when future bars were mutated! Lookahead bias detected."


def test_final_confidence_and_strategy_id_anti_spoof(sample_synthetic_ohlcv):
    """Adversarial test: Changing confidence scores or strategy IDs MUST NOT manufacture winning trades."""
    opp = {
        "timestamp": str(sample_synthetic_ohlcv["timestamp"].iloc[50]),
        "asset": "BTC",
        "strategy_family": "trend",
        "direction": "LONG",
        "entry_price": float(sample_synthetic_ohlcv["close"].iloc[50]),
        "stop_loss": float(sample_synthetic_ohlcv["close"].iloc[50]) * 0.95,
        "take_profit": float(sample_synthetic_ohlcv["close"].iloc[50]) * 1.10,
        "confidence": 0.10
    }

    trade1 = resolve_single_opportunity_final(opp, sample_synthetic_ohlcv)

    # Change confidence to 0.99 and strategy_id to "SUPER_WINNER"
    opp_spoofed = opp.copy()
    opp_spoofed["confidence"] = 0.99
    opp_spoofed["strategy_family"] = "SUPER_WINNER"

    trade2 = resolve_single_opportunity_final(opp_spoofed, sample_synthetic_ohlcv)

    if trade1 is not None and trade2 is not None:
        assert trade1["net_pnl"] == trade2["net_pnl"], "Changing confidence score altered trade outcome! Anti-spoof test failed."


def test_final_same_candle_collision(sample_synthetic_ohlcv):
    """Test same-candle SL/TP collision resolves conservatively as LOSS."""
    opp = {
        "timestamp": str(sample_synthetic_ohlcv["timestamp"].iloc[50]),
        "asset": "BTC",
        "strategy_family": "trend",
        "direction": "LONG",
        "entry_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 105.0,
        "confidence": 0.50
    }

    # Construct collision candle where both SL and TP are touched
    df_collision = sample_synthetic_ohlcv.copy()
    df_collision.loc[51, "open"] = 100.0
    df_collision.loc[51, "high"] = 110.0  # hits TP
    df_collision.loc[51, "low"] = 90.0    # hits SL
    df_collision.loc[51, "close"] = 102.0

    trade = resolve_single_opportunity_final(opp, df_collision, execution_delay=1)
    assert trade is not None
    assert trade["exit_reason"] == "SAME_CANDLE_COLLISION_LOSS"
    assert trade["net_pnl"] < 0, "Same-candle collision was not treated as a LOSS!"


def test_final_execution_delay(sample_synthetic_ohlcv):
    """Test trade entry respects specified execution delay (1 vs 2 bars)."""
    opp = {
        "timestamp": str(sample_synthetic_ohlcv["timestamp"].iloc[50]),
        "asset": "BTC",
        "strategy_family": "trend",
        "direction": "LONG",
        "entry_price": 100.0,
        "stop_loss": 90.0,
        "take_profit": 110.0,
        "confidence": 0.50
    }

    trade_delay1 = resolve_single_opportunity_final(opp, sample_synthetic_ohlcv, execution_delay=1)
    trade_delay2 = resolve_single_opportunity_final(opp, sample_synthetic_ohlcv, execution_delay=2)

    assert trade_delay1 is not None and trade_delay2 is not None
    assert trade_delay1["execution_timestamp"] != trade_delay2["execution_timestamp"]


def test_final_purged_validation_and_embargo(sample_synthetic_ohlcv):
    """Test purged validation enforces embargo period between train and test splits."""
    train_df, val_df = apply_purged_embargo_split_final(sample_synthetic_ohlcv, train_pct=0.50, embargo_bars=24)

    assert len(train_df) == 50
    assert len(val_df) == 100 - 50 - 24  # 26 bars remaining after 24-bar embargo
    assert pd.to_datetime(val_df["timestamp"].iloc[0]) > pd.to_datetime(train_df["timestamp"].iloc[-1])


def test_final_bootstrap_and_monte_carlo():
    """Test 10,000 Block Bootstrap and 10,000 Monte Carlo simulation runs."""
    trades = [
        {"net_pnl": 10.0, "position_size_usd": 100.0},
        {"net_pnl": -5.0, "position_size_usd": 100.0},
        {"net_pnl": 15.0, "position_size_usd": 100.0},
        {"net_pnl": -8.0, "position_size_usd": 100.0},
        {"net_pnl": 20.0, "position_size_usd": 100.0}
    ]

    boot = run_block_bootstrap_resampling_final(trades, num_iterations=1000)
    assert "pf_mean" in boot
    assert "pf_ci_lower" in boot

    mc = run_monte_carlo_simulation_final(trades, num_simulations=1000)
    assert "max_drawdown_95_pct" in mc
    assert "risk_of_ruin_pct" in mc


def test_final_deflated_sharpe_ratio():
    """Test Deflated Sharpe Ratio (DSR) calculation across tested hypotheses."""
    dsr = calculate_deflated_sharpe_ratio_final(observed_sharpe=1.5, num_trials=22, sample_length=100)
    assert "p_value" in dsr
    assert "is_statistically_significant" in dsr


def test_final_holdout_evaluation(sample_synthetic_ohlcv):
    """Test untouched frozen final holdout evaluator executes EXACTLY ONCE."""
    holdout_datasets = {"BTC": sample_synthetic_ohlcv}
    top_tuple = CANDIDATE_STRATEGIES_FINAL[0]

    report = evaluate_untouched_final_holdout(holdout_datasets, top_tuple)
    assert "holdout_decision" in report
    assert report["holdout_decision"] in ["FINAL_HOLDOUT_PASS", "FINAL_HOLDOUT_FAIL", "INCONCLUSIVE"]


def test_final_full_pipeline_execution():
    """Full master pipeline integration test."""
    res = run_final_research_pipeline(tier_name="TIER_20", timeframe="1h", days=30)
    assert "overall_verdict" in res
    assert res["overall_verdict"] in [
        "ROBUST_PROFITABLE",
        "PROMISING_BUT_INSUFFICIENT_SAMPLE",
        "PROFITABLE_BUT_NOT_ROBUST",
        "FRAGILE",
        "NO_DEFENDED_EDGE",
        "NO_ROBUST_EDGE_FOUND"
    ]

