"""
Rolling Walk-Forward Engine for NEXUS-7 Research Reset.
Implements Train -> Validate -> Unseen Test rolling window partitioning.
Ensures unseen test data NEVER influences feature selection or strategy decisions.
"""
import dataclasses
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from app.config import Settings
from backtest.metrics import BacktestReport, compute_report
from backtest.mock_ai_analyst import MockAiAnalyst
from backtest.simulator import BacktestSimulator


@dataclass
class WalkForwardWindowResult:
    window_id: int
    train_bars: int
    val_bars: int
    test_bars: int
    train_pf: float
    val_pf: float
    test_pf: float
    test_trades: int
    test_win_rate_pct: float
    test_net_pnl_usd: float
    test_expectancy_usd: float


def run_rolling_walk_forward(
    candles_1h: list,
    symbol: str,
    strategy_obj,
    base_settings: Settings,
    train_bars: int = 4380,  # ~6 months
    val_bars: int = 1460,    # ~2 months
    test_bars: int = 1460,   # ~2 months
    step_bars: int = 1460,   # ~2 months step
) -> List[WalkForwardWindowResult]:
    """
    Executes rolling Train -> Validate -> Unseen Test walk-forward analysis.
    """
    df_candles = pd.DataFrame(candles_1h, columns=["ts", "open", "high", "low", "close", "volume"])
    signals = strategy_obj.generate_signals(df_candles)

    total_bars = len(candles_1h)
    window_results = []
    w_id = 1
    start_idx = 0

    cand_c_settings = dataclasses.replace(base_settings, timeframe="1h", min_volume_ratio=0.7, min_confidence_score=90)
    analyst = MockAiAnalyst(mode="ai_mirror", seed=42)

    def sim_subset(sub_candles: list, sub_signals: pd.Series) -> List:
        sim = BacktestSimulator(
            candles=sub_candles,
            symbol=symbol,
            analyst=analyst,
            settings_obj=cand_c_settings,
            initial_equity=10000.0,
            fee_pct=0.04,  # Base execution friction
            slippage_pct=0.01,
            execution_mode="maker",
            enable_4h_trend_filter=True,
            enable_4h_chop_filter=True,
        )
        import asyncio
        return asyncio.run(sim.run())

    while (start_idx + train_bars + val_bars + test_bars) <= total_bars:
        train_end = start_idx + train_bars
        val_end = train_end + val_bars
        test_end = val_end + test_bars

        train_c = candles_1h[start_idx:train_end]
        val_c = candles_1h[train_end:val_end]
        test_c = candles_1h[val_end:test_end]

        tr_train = sim_subset(train_c, signals.iloc[start_idx:train_end])
        tr_val = sim_subset(val_c, signals.iloc[train_end:val_end])
        tr_test = sim_subset(test_c, signals.iloc[val_end:test_end])

        rep_train = compute_report(tr_train, 10000.0, f"WF_{w_id}_Train", symbol, "1h", len(train_c), 0)
        rep_val = compute_report(tr_val, 10000.0, f"WF_{w_id}_Val", symbol, "1h", len(val_c), 0)
        rep_test = compute_report(tr_test, 10000.0, f"WF_{w_id}_Test", symbol, "1h", len(test_c), 0)

        window_results.append(WalkForwardWindowResult(
            window_id=w_id,
            train_bars=len(train_c),
            val_bars=len(val_c),
            test_bars=len(test_c),
            train_pf=rep_train.profit_factor,
            val_pf=rep_val.profit_factor,
            test_pf=rep_test.profit_factor,
            test_trades=rep_test.total_trades,
            test_win_rate_pct=rep_test.win_rate_pct,
            test_net_pnl_usd=rep_test.net_pnl_usd,
            test_expectancy_usd=rep_test.expectancy_usd,
        ))

        w_id += 1
        start_idx += step_bars

    return window_results
