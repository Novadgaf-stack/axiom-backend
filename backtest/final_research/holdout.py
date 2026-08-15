"""
Untouched Frozen Final Holdout Evaluator Module for NEXUS-7 Final Master Research
Evaluates the frozen top strategy candidate on the 20% untouched final holdout dataset EXACTLY ONCE.
Strictly prohibits parameter modification or retuning after holdout inspection.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from backtest.final_research.candle_resolver import resolve_single_opportunity_final
from backtest.final_research.opportunity_selector import generate_candidate_opportunities_final
from backtest.final_research.statistical_evaluator import evaluate_trade_statistics_final
from backtest.final_research.bootstrap import run_block_bootstrap_resampling_final
from backtest.final_research.monte_carlo import run_monte_carlo_simulation_final


def evaluate_untouched_final_holdout(
    holdout_datasets: Dict[str, pd.DataFrame],
    top_strategy_entry: tuple
) -> Dict[str, Any]:
    """
    Runs frozen top strategy against untouched 20% final holdout dataset EXACTLY ONCE.
    """
    strat_name, tf, family, strat_fn = top_strategy_entry

    all_holdout_opps = generate_candidate_opportunities_final(
        holdout_datasets,
        strat_fn,
        family_name=family,
        timeframe=tf
    )

    holdout_trades = []
    for opp in all_holdout_opps:
        asset = opp["asset"]
        if asset in holdout_datasets:
            df = holdout_datasets[asset]
            t = resolve_single_opportunity_final(opp, df)
            if t is not None:
                holdout_trades.append(t)

    stats = evaluate_trade_statistics_final(holdout_trades, total_days=12.0)
    boot = run_block_bootstrap_resampling_final(holdout_trades, num_iterations=10000)
    mc = run_monte_carlo_simulation_final(holdout_trades, num_simulations=10000)

    pf = stats.get("profit_factor", 0.0)
    n = stats.get("trade_count", 0)

    if pf > 1.0 and n >= 10 and boot.get("pf_ci_lower", 0.0) > 1.0:
        decision = "FINAL_HOLDOUT_PASS"
    elif n == 0 or pf == 0.0:
        decision = "INCONCLUSIVE"
    else:
        decision = "FINAL_HOLDOUT_FAIL"

    return {
        "strategy_name": strat_name,
        "timeframe": tf,
        "family": family,
        "holdout_decision": decision,
        "trade_count": n,
        "trades_per_day": stats.get("trades_per_day", 0.0),
        "profit_factor": stats.get("profit_factor", 0.0),
        "net_expectancy_usd": stats.get("net_expectancy_usd", 0.0),
        "win_rate_pct": stats.get("win_rate_pct", 0.0),
        "max_drawdown_pct": stats.get("max_drawdown_pct", 0.0),
        "bootstrap_ci": [boot.get("pf_ci_lower", 0.0), boot.get("pf_ci_upper", 0.0)],
        "monte_carlo_dd_95": mc.get("max_drawdown_95_pct", 0.0),
        "trades": holdout_trades
    }
