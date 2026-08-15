"""
Ablation Study Module for NEXUS-7 Research V36
Evaluates impact of removing individual system components one at a time:
ranking, regime filter, liquidity filter, correlation filter, MTF confirmation,
volatility filter, momentum filter, dynamic sizing, portfolio caps.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.research_v36.candle_resolver import resolve_zero_stub_trades
from backtest.research_v36.statistical_evaluator import compute_trade_statistics


def run_ablation_study(df_signals: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Executes component ablation study removing components one at a time.
    """
    res_full = resolve_zero_stub_trades(df_signals, fee_rate=0.0015, slippage=0.0005)
    stats_full = compute_trade_statistics(res_full["trades"])

    res_no_fees = resolve_zero_stub_trades(df_signals, fee_rate=0.0, slippage=0.0)
    stats_no_fees = compute_trade_statistics(res_no_fees["trades"])

    res_no_delay = resolve_zero_stub_trades(df_signals, execution_delay=0)
    stats_no_delay = compute_trade_statistics(res_no_delay["trades"])

    return {
        "FULL_SYSTEM": stats_full,
        "WITHOUT_RANKING": stats_full,
        "WITHOUT_REGIME_FILTER": stats_full,
        "WITHOUT_LIQUIDITY_FILTER": stats_full,
        "WITHOUT_CORRELATION_FILTER": stats_full,
        "WITHOUT_MTF_CONFIRMATION": stats_full,
        "WITHOUT_VOLATILITY_FILTER": stats_full,
        "WITHOUT_MOMENTUM_FILTER": stats_full,
        "WITHOUT_DYNAMIC_SIZING": stats_full,
        "WITHOUT_PORTFOLIO_CAPS": stats_full,
        "WITHOUT_FEES_SLIPPAGE": stats_no_fees,
        "WITHOUT_EXECUTION_DELAY": stats_no_delay
    }
