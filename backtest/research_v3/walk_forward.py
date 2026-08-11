"""
NEXUS-7 — RESEARCH V3 ROLLING WALK-FORWARD VALIDATION MODULE
Evaluates strategy candidates across multiple rolling out-of-sample windows.
"""
import pandas as pd
import numpy as np


def run_rolling_walk_forward_v3(
    universe_candles: dict[str, list[dict]],
    strategy,
    run_backtest_fn,
    settings_obj,
    num_windows: int = 4,
    fee_pct: float = 0.04,
    slippage_pct: float = 0.01
) -> dict:
    """
    Splits data into N rolling walk-forward windows and evaluates OOS stability.
    """
    pair = "BTCUSDT" if "BTCUSDT" in universe_candles else list(universe_candles.keys())[0]
    full_candles = universe_candles[pair]
    total_len = len(full_candles)
    
    if total_len < 100:
        return {
            "num_windows": num_windows,
            "pct_profitable_windows": 0.0,
            "median_pf": 0.0,
            "mean_pf": 0.0,
            "median_expectancy": 0.0,
            "best_window_pf": 0.0,
            "worst_window_pf": 0.0,
            "oos_sharpe": 0.0,
            "max_drawdown_pct": 0.0
        }
        
    window_size = total_len // (num_windows + 1)
    window_pfs = []
    window_pnl_list = []
    
    for w in range(num_windows):
        train_start = w * (window_size // 2)
        test_start = train_start + window_size
        test_end = min(total_len, test_start + window_size)
        
        test_candles = full_candles[test_start:test_end]
        if len(test_candles) < 30:
            continue
            
        df_test = pd.DataFrame(test_candles, columns=["ts", "open", "high", "low", "close", "volume"])
        sig_test = strategy.generate_signals(df_test, symbol=pair)
        
        trades = run_backtest_fn(test_candles, pair, sig_test, settings_obj, fee_pct=fee_pct, slippage_pct=slippage_pct)
        
        if not trades:
            window_pfs.append(0.0)
            window_pnl_list.append(0.0)
            continue
            
        wins = [t.pnl_usd for t in trades if t.pnl_usd > 0]
        losses = [abs(t.pnl_usd) for t in trades if t.pnl_usd < 0]
        
        sum_wins = sum(wins)
        sum_losses = sum(losses)
        
        pf = (sum_wins / sum_losses) if sum_losses > 0 else (2.0 if sum_wins > 0 else 0.0)
        net_pnl = sum([t.pnl_usd for t in trades])
        
        window_pfs.append(pf)
        window_pnl_list.append(net_pnl)
        
    if not window_pfs:
        return {
            "num_windows": num_windows,
            "pct_profitable_windows": 0.0,
            "median_pf": 0.0,
            "mean_pf": 0.0,
            "median_expectancy": 0.0,
            "best_window_pf": 0.0,
            "worst_window_pf": 0.0,
            "oos_sharpe": 0.0,
            "max_drawdown_pct": 0.0
        }
        
    prof_windows = sum([1 for pf in window_pfs if pf > 1.0])
    pct_prof = (prof_windows / len(window_pfs)) * 100.0
    
    median_pf = float(np.median(window_pfs))
    mean_pf = float(np.mean(window_pfs))
    best_pf = float(np.max(window_pfs))
    worst_pf = float(np.min(window_pfs))
    median_exp = float(np.median(window_pnl_list))
    
    std_pnl = np.std(window_pnl_list)
    oos_sharpe = float(np.mean(window_pnl_list) / (std_pnl + 1e-8)) if std_pnl > 0 else 0.0
    
    return {
        "num_windows": len(window_pfs),
        "pct_profitable_windows": round(pct_prof, 2),
        "median_pf": round(median_pf, 2),
        "mean_pf": round(mean_pf, 2),
        "median_expectancy": round(median_exp, 2),
        "best_window_pf": round(best_pf, 2),
        "worst_window_pf": round(worst_pf, 2),
        "oos_sharpe": round(oos_sharpe, 3),
        "max_drawdown_pct": 0.0
    }
