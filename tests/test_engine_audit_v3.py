"""
Unit test verifying that zero-signal strategies are classified as 'INSUFFICIENT DATA'
in the V3 Research Engine Audit.
"""
import pandas as pd
import pytest
from backtest.research_v3.engine_audit import run_engine_audit_v3


class MockZeroSignalStrategy:
    def __init__(self):
        self.exp_id = "EXP-TEST-01"
        self.name = "Mock Zero Signal Strategy"

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        # Returns all zero signals
        return pd.Series(0, index=df.index)


class MockActiveSignalStrategy:
    def __init__(self):
        self.exp_id = "EXP-TEST-02"
        self.name = "Mock Active Signal Strategy"

    def generate_signals(self, df: pd.DataFrame, symbol: str = "BTCUSDT") -> pd.Series:
        s = pd.Series(0, index=df.index)
        if len(s) > 10:
            s.iloc[5] = 1
            s.iloc[10] = -1
        return s


def test_zero_signal_classification_is_insufficient_data():
    candles = [
        {"ts": 1000000 + i * 3600000, "open": 50000 + i, "high": 50100 + i, "low": 49900 + i, "close": 50050 + i, "volume": 100}
        for i in range(20)
    ]
    universe = {"BTCUSDT": candles}
    
    strats = [MockZeroSignalStrategy(), MockActiveSignalStrategy()]
    df_results, _ = run_engine_audit_v3(universe, strats)
    
    zero_row = df_results[df_results["exp_id"] == "EXP-TEST-01"].iloc[0]
    active_row = df_results[df_results["exp_id"] == "EXP-TEST-02"].iloc[0]
    
    # Assert zero-signal strategy verdict is INSUFFICIENT DATA, not PASSED
    assert zero_row["total_signals"] == 0
    assert zero_row["uniqueness_verdict"] == "INSUFFICIENT DATA"
    
    # Assert active strategy with unique signals passes
    assert active_row["total_signals"] == 2
    assert active_row["uniqueness_verdict"] == "PASSED (Independent)"
