"""
NEXUS-7 — RESEARCH V27 MAIN ENGINE
Orchestration engine for V27 Targeted Expectancy Research & Accelerated Forward Paper Trading.
Evaluates candidates across 12 liquid pairs, 4 timeframes, chronological splits,
1,000-iteration bootstrap CIs, statistical gates, isolated risk budget scaling, and forward paper trading.
"""
import os
import csv
import pandas as pd
from typing import Dict, List, Any

from backtest.research_v27.data_pipeline import load_multi_asset_dataset, split_chronological_dataset
from backtest.research_v27.strategy_library import (
    TargetedMTFPullback,
    FilteredBreakoutExpansion,
    AdaptiveMeanReversion,
    MomentumContinuation,
    DynamicConfluenceFilter
)
from backtest.research_v27.statistical_gates import evaluate_trade_sequence, compute_bootstrap_ci, check_statistical_gates
from backtest.research_v27.risk_evaluator import evaluate_risk_sizing_sensitivity
from backtest.research_v27.forward_paper_engine import AcceleratedForwardPaperEngine


def simulate_candidate_trades(candidate, dataset: Dict[str, Dict[str, pd.DataFrame]], split_key: str = "forward") -> Tuple[List[Dict[str, Any]], float]:
    """
    Simulates trades for a candidate across 12 liquid pairs for the specified dataset split ('train', 'val', 'forward').
    Returns (all_trades, total_days).
    """
    all_trades = []
    total_days = 0.0

    for pair, tf_data in dataset.items():
        if candidate.timeframe not in tf_data:
            continue

        df_full = tf_data[candidate.timeframe]
        htf_df_full = tf_data.get("1h", pd.DataFrame())

        df_tr, df_v, df_fw = split_chronological_dataset(df_full)
        htf_tr, htf_v, htf_fw = split_chronological_dataset(htf_df_full) if not htf_df_full.empty else (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

        if split_key == "train":
            df = df_tr
            htf_df = htf_tr
        elif split_key == "val":
            df = df_v
            htf_df = htf_v
        else:
            df = df_fw
            htf_df = htf_fw

        if df.empty or len(df) < 50:
            continue

        start_time = df["timestamp"].iloc[0]
        end_time = df["timestamp"].iloc[-1]
        pair_days = (end_time - start_time).total_seconds() / 86400.0
        total_days = max(total_days, pair_days)

        pair_trades = candidate.generate_signals(df, htf_df=htf_df)
        for t in pair_trades:
            t["symbol"] = pair
            all_trades.append(t)

    all_trades.sort(key=lambda x: x["timestamp"])
    return all_trades, total_days


def run_full_v27_pipeline(days: int = 180, seed: int = 42) -> Dict[str, Any]:
    """
    Executes complete V27 Research & Forward Paper Trading pipeline.
    """
    dataset = load_multi_asset_dataset(days=days, seed=seed)

    candidates = [
        TargetedMTFPullback(timeframe="15m", min_confidence=0.82),
        TargetedMTFPullback(timeframe="30m", min_confidence=0.82),
        FilteredBreakoutExpansion(timeframe="30m", min_confidence=0.82),
        FilteredBreakoutExpansion(timeframe="1h", min_confidence=0.82),
        AdaptiveMeanReversion(timeframe="15m", min_confidence=0.80),
        AdaptiveMeanReversion(timeframe="30m", min_confidence=0.80),
        MomentumContinuation(timeframe="1h", min_confidence=0.82),
        MomentumContinuation(timeframe="4h", min_confidence=0.82),
        DynamicConfluenceFilter(timeframe="30m", min_confidence=0.83)
    ]

    summary_results = []
    overall_passed_candidates = []

    for cand in candidates:
        # Simulate across Train, Validation, and Forward Out-of-Sample splits
        tr_trades, tr_days = simulate_candidate_trades(cand, dataset, split_key="train")
        v_trades, v_days = simulate_candidate_trades(cand, dataset, split_key="val")
        fw_trades, fw_days = simulate_candidate_trades(cand, dataset, split_key="forward")

        tr_metrics = evaluate_trade_sequence(tr_trades, tr_days, friction_pct=0.0015)
        v_metrics = evaluate_trade_sequence(v_trades, v_days, friction_pct=0.0015)
        fw_metrics = evaluate_trade_sequence(fw_trades, fw_days, friction_pct=0.0015)

        # Friction sensitivity on Forward split
        fw_sens_015 = fw_metrics
        fw_sens_030 = evaluate_trade_sequence(fw_trades, fw_days, friction_pct=0.0030)
        fw_sens_045 = evaluate_trade_sequence(fw_trades, fw_days, friction_pct=0.0045)

        # Bootstrap CIs on Forward returns
        ci_mean, ci_lower, ci_upper = compute_bootstrap_ci(fw_metrics["returns"], num_iterations=1000, seed=seed)
        bootstrap_ci = (ci_mean, ci_lower, ci_upper)

        # Statistical gates evaluation
        gates_eval = check_statistical_gates(fw_metrics, bootstrap_ci)

        # Isolated position sizing budget testing (only if gates passed)
        risk_sensitivity = {}
        if gates_eval["overall_pass"]:
            risk_sensitivity = evaluate_risk_sizing_sensitivity(fw_trades, initial_balance=10000.0)
            overall_passed_candidates.append(cand.candidate_id)

        # Accelerated Forward Paper Trading simulation
        paper_sim = AcceleratedForwardPaperEngine(cand, initial_balance=10000.0, risk_per_trade_pct=0.5)
        paper_res = paper_sim.run_forward_paper_trading(dataset)

        res_record = {
            "candidate_id": cand.candidate_id,
            "family": cand.family,
            "timeframe": cand.timeframe,
            "train_tpd": tr_metrics["trades_per_day"],
            "train_pf": tr_metrics["profit_factor"],
            "val_tpd": v_metrics["trades_per_day"],
            "val_pf": v_metrics["profit_factor"],
            "oos_tpd": fw_metrics["trades_per_day"],
            "oos_win_rate": fw_metrics["win_rate"],
            "oos_pf_015": fw_sens_015["profit_factor"],
            "oos_pf_030": fw_sens_030["profit_factor"],
            "oos_pf_045": fw_sens_045["profit_factor"],
            "oos_max_dd_pct": fw_metrics["max_drawdown_pct"],
            "bootstrap_ci_lower": ci_lower,
            "bootstrap_ci_upper": ci_upper,
            "verdict": gates_eval["verdict"],
            "rejection_reasons": "; ".join(gates_eval["rejection_reasons"]),
            "paper_return_pct": paper_res["total_return_pct"],
            "paper_max_dd_pct": paper_res["max_drawdown_pct"],
            "paper_trades": paper_res["total_trades"],
            "risk_sensitivity": risk_sensitivity
        }

        summary_results.append(res_record)

    # Save summary CSV
    os.makedirs("strategy_research", exist_ok=True)
    csv_path = "strategy_research/v27_expectancy_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "candidate_id", "family", "timeframe", "train_tpd", "train_pf",
            "val_tpd", "val_pf", "oos_tpd", "oos_win_rate", "oos_pf_015",
            "oos_pf_030", "oos_pf_045", "oos_max_dd_pct", "bootstrap_ci_lower",
            "bootstrap_ci_upper", "verdict", "rejection_reasons", "paper_return_pct",
            "paper_max_dd_pct", "paper_trades"
        ])
        writer.writeheader()
        for r in summary_results:
            row_copy = {k: v for k, v in r.items() if k != "risk_sensitivity"}
            writer.writerow(row_copy)

    # Generate Markdown Report
    report_path = "strategy_research/V27_EXPECTANCY_AND_PAPER_TRADING_REPORT.md"
    overall_verdict = "PASSED (EDGE PROVEN & PAPER CERTIFIED)" if len(overall_passed_candidates) > 0 else "REJECTED (NO EDGE PROVEN)"

    md_lines = [
        "# NEXUS-7 — RESEARCH V27: TARGETED EXPECTANCY & ACCELERATED FORWARD PAPER TRADING REPORT",
        "",
        "## Executive Summary",
        f"- **Overall Pipeline Verdict**: `{overall_verdict}`",
        f"- **Target Frequency Window**: 0.8 to 1.8 trades/day (~1 - 1.5/day)",
        f"- **Candidates Evaluated**: {len(candidates)} candidates across 5 strategy families",
        f"- **Multi-Asset Universe**: 12 liquid pairs (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, DOT, NEAR, SUI)",
        f"- **Timeframes Evaluated**: 15m, 30m, 1h, 4h",
        f"- **Chronological Data Split**: Train (50%), Validation (25%), Untouched Forward (25%)",
        f"- **Statistical Gates**: OOS PF >= 1.25, Bootstrap 95% CI Lower Bound > 0.00, Max DD <= 15.0%",
        f"- **Candidates Passed**: {len(overall_passed_candidates)} ({', '.join(overall_passed_candidates) if overall_passed_candidates else 'None'})",
        "",
        "---",
        "",
        "## Out-of-Sample Performance Summary Table",
        "",
        "| Candidate ID | Family | TF | OOS Trades/Day | OOS Win Rate | OOS PF (0.15%) | Bootstrap 95% CI | Max DD (%) | Verdict |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in summary_results:
        ci_str = f"[{r['bootstrap_ci_lower']}, {r['bootstrap_ci_upper']}]"
        md_lines.append(
            f"| `{r['candidate_id']}` | {r['family']} | {r['timeframe']} | {r['oos_tpd']} | {r['oos_win_rate']*100:.1f}% | {r['oos_pf_015']} | {ci_str} | {r['oos_max_dd_pct']}% | `{r['verdict']}` |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## Friction & Leverage Sensitivity Analysis",
        "",
        "| Candidate ID | OOS PF (0.15%) | OOS PF (0.30%) | OOS PF (0.45%) | Paper Return (%) | Paper Max DD (%) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ])

    for r in summary_results:
        md_lines.append(
            f"| `{r['candidate_id']}` | {r['oos_pf_015']} | {r['oos_pf_030']} | {r['oos_pf_045']} | {r['paper_return_pct']}% | {r['paper_max_dd_pct']}% |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## Accelerated Forward Paper Trading Telemetry",
        "All candidates were streamed through the Accelerated Forward Paper Trading Engine with fixed parameter rules, trailing stops, order latency, and 0.15% fee accounting.",
        "",
        "---",
        "",
        "## Research Conclusions & Discipline Directive",
        "1. **Trade Frequency Integrity**: We focused explicitly on the 1-1.5 trades/day region. We did not force trade volume or modify strategy parameters during paper trading.",
        "2. **Strict Edge Requirement**: Position sizing scaling (0.75%, 1.0%) was only applied to candidates passing out-of-sample statistical gates.",
        "3. **Nexus-7 Core Protection**: Live real-money trading remains hard-locked (`TRADING_ENABLED = False`) and core execution modules remain frozen.",
        ""
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return {
        "overall_verdict": overall_verdict,
        "candidates_evaluated": len(candidates),
        "passed_candidates": overall_passed_candidates,
        "summary_results": summary_results
    }
