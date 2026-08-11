"""
NEXUS-7 — RESEARCH V3 3-TIER COST STRESS TESTER
Evaluates candidates under Base (1.0x), Intermediate (1.5x), and Severe (2.0x) fee/slippage friction.
"""
import pandas as pd
import numpy as np


def run_cost_stress_test_v3(
    universe_candles: dict[str, list[dict]],
    strategy,
    run_backtest_fn,
    settings_obj
) -> list[dict]:
    """
    Evaluates candidate strategy across 1.0x, 1.5x, and 2.0x cost tiers.
    """
    cost_tiers = [
        {"tier_name": "1.0x (Base Costs)", "fee_pct": 0.04, "slippage_pct": 0.01},
        {"tier_name": "1.5x (Intermediate)", "fee_pct": 0.06, "slippage_pct": 0.015},
        {"tier_name": "2.0x (Severe Friction)", "fee_pct": 0.08, "slippage_pct": 0.02},
    ]
    
    results = []
    pair = "BTCUSDT" if "BTCUSDT" in universe_candles else list(universe_candles.keys())[0]
    candles = universe_candles[pair]
    df = pd.DataFrame(candles, columns=["ts", "open", "high", "low", "close", "volume"])
    signals = strategy.generate_signals(df, symbol=pair)
    
    base_pf = 0.0
    
    for tier in cost_tiers:
        trades = run_backtest_fn(candles, pair, signals, settings_obj, fee_pct=tier["fee_pct"], slippage_pct=tier["slippage_pct"])
        
        n_trades = len(trades)
        if n_trades == 0:
            results.append({
                "exp_id": strategy.exp_id,
                "strategy_name": strategy.name,
                "cost_tier": tier["tier_name"],
                "fee_pct": tier["fee_pct"],
                "slippage_pct": tier["slippage_pct"],
                "n_trades": 0,
                "win_rate_pct": 0.0,
                "pf": 0.0,
                "net_pnl_usd": 0.0,
                "expectancy_usd": 0.0,
                "cost_degradation_pct": 0.0,
                "verdict": "INSUFFICIENT DATA"
            })
            continue
            
        wins = [t.pnl_usd for t in trades if t.pnl_usd > 0]
        losses = [abs(t.pnl_usd) for t in trades if t.pnl_usd < 0]
        
        sum_wins = sum(wins)
        sum_losses = sum(losses)
        
        pf = (sum_wins / sum_losses) if sum_losses > 0 else (2.0 if sum_wins > 0 else 0.0)
        net_pnl = sum([t.pnl_usd for t in trades])
        expectancy = net_pnl / n_trades
        win_rate = (len(wins) / n_trades) * 100.0
        
        if tier["fee_pct"] == 0.04:
            base_pf = pf
            deg_pct = 0.0
        else:
            deg_pct = round(((pf - base_pf) / (base_pf + 1e-8)) * 100.0, 2)
            
        verdict = "PASSED" if pf >= 1.10 and expectancy > 0 else "REJECTED"
        
        results.append({
            "exp_id": strategy.exp_id,
            "strategy_name": strategy.name,
            "cost_tier": tier["tier_name"],
            "fee_pct": tier["fee_pct"],
            "slippage_pct": tier["slippage_pct"],
            "n_trades": n_trades,
            "win_rate_pct": round(win_rate, 2),
            "pf": round(pf, 2),
            "net_pnl_usd": round(net_pnl, 2),
            "expectancy_usd": round(expectancy, 2),
            "cost_degradation_pct": deg_pct,
            "verdict": verdict
        })
        
    return results
