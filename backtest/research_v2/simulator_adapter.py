"""
Simulator Integration Adapter for Research V2.
Allows BacktestSimulator to directly execute external strategy signal vectors.
"""
import dataclasses
from typing import List, Optional
import pandas as pd

from app.config import Settings
from backtest.metrics import SimTrade
from backtest.mock_ai_analyst import MockAiAnalyst
from backtest.simulator import BacktestSimulator


from app.ai_analyst import AnalystResult, GeminiDecision


def run_custom_signal_backtest(
    candles: list,
    symbol: str,
    signals: pd.Series,
    settings_obj: Settings,
    fee_pct: float = 0.04,
    slippage_pct: float = 0.01,
    execution_mode: str = "maker",
) -> List[SimTrade]:
    """
    Executes a backtest driven directly by an external signal Series (BUY = 1, SELL = -1, HOLD = 0).
    """
    import asyncio
    
    # Custom analyst that reads external signal vector directly
    class CustomSignalAnalyst(MockAiAnalyst):
        def __init__(self, sig_series: pd.Series, start_bar: int = 36):
            super().__init__(mode="ai_mirror", seed=42)
            self.sig_series = sig_series.reset_index(drop=True)
            self.current_bar_idx = start_bar

        async def analyze(self, *args, **kwargs):
            idx = self.current_bar_idx
            self.current_bar_idx += 1
            
            sig = 0
            if 0 <= idx < len(self.sig_series):
                sig = self.sig_series.iloc[idx]
            
            if sig == 1:
                gd = GeminiDecision(decision="BUY", confidence_score=95, approved=True, risk_flags=[], reasoning="Custom Signal BUY")
                return AnalystResult(decision=gd, raw_text="{}", error=None)
            elif sig == -1:
                gd = GeminiDecision(decision="SELL", confidence_score=95, approved=True, risk_flags=[], reasoning="Custom Signal SELL")
                return AnalystResult(decision=gd, raw_text="{}", error=None)
            
            gd = GeminiDecision(decision="HOLD", confidence_score=0, approved=False, risk_flags=[], reasoning="No Signal")
            return AnalystResult(decision=gd, raw_text="{}", error=None)

    cand_c_settings = dataclasses.replace(
        settings_obj,
        timeframe="1h",
        min_volume_ratio=0.0,
        min_confidence_score=90,
        require_technical_confirmation=False,
        enable_session_filter=False,
        min_adx=0.0,
    )
    analyst_adapter = CustomSignalAnalyst(signals)

    sim = BacktestSimulator(
        candles=candles,
        symbol=symbol,
        analyst=analyst_adapter,
        settings_obj=cand_c_settings,
        initial_equity=10000.0,
        fee_pct=fee_pct,
        slippage_pct=slippage_pct,
        execution_mode=execution_mode,
        enable_4h_trend_filter=False,  # Signal generator handles regime filtering directly
        enable_4h_chop_filter=False,
    )

    return asyncio.run(sim.run())
