"""
NEXUS-7 — RESEARCH V26 ENGINE
Full Research Pipeline for V26 Optimized Expectancy Research.
Evaluates candidates across liquid pairs, timeframes, chronological data splits (Train 50%, Val 25%, Forward 25%),
friction sensitivity (0.15%, 0.30%, 0.45%), bootstrap CIs, and post-gate position sizing sensitivity (0.5%, 0.75%, 1.0%).
"""
import os
import csv
import random
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from backtest.research_v26.data_pipeline import load_multi_asset_dataset, split_chronological_dataset
from backtest.research_v26.strategy_library import (
    SUPPORTED_PAIRS,
    TIMEFRAMES,
    MTFTrendPullback,
    BreakoutVolumeExpansion,
    AdaptiveMeanReversion,
    MomentumContinuation,
    DynamicRegimeFilter
)
from backtest.research_v26.statistical_gates import evaluate_trade_sequence, check_statistical_gates
from backtest.research_v26.risk_evaluator import evaluate_risk_sizing_sensitivity


def simulate_candidate_trades(candidate, dataset: Dict[str, Dict[str, pd.DataFrame]], split_key: str = "forward") -> Tuple[List[Dict[str, Any]], float]:
    """
    Simulates trades for a candidate across 9 liquid pairs for the specified dataset split ('train', 'val', 'forward').
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

        sig_df = candidate.generate_signals(df, htf_df)

        # Simulate trades with ATR-based stop-loss / take-profit
        in_pos = False
        entry_price = 0.0
        atr_entry = 0.0
        pos_dir = 0

        for i in range(len(sig_df)):
            row = sig_df.iloc[i]
            sig = int(row.get("signal", 0))
            close = float(row["close"])
            atr = float(row.get("atr", close * 0.01))

            if not in_pos:
                if sig != 0:
                    in_pos = True
                    entry_price = close
                    atr_entry = max(atr, close * 0.005)
                    pos_dir = sig
            else:
                # Target 2.0 R / Risk 1.0 R
                tp = entry_price + (pos_dir * 2.0 * atr_entry)
                sl = entry_price - (pos_dir * 1.0 * atr_entry)

                hit_tp = (row["high"] >= tp) if pos_dir == 1 else (row["low"] <= tp)
                hit_sl = (row["low"] <= sl) if pos_dir == 1 else (row["high"] >= sl)
                sig_exit = (sig == -pos_dir)

                if hit_tp or hit_sl or sig_exit:
                    if hit_tp:
                        raw_r = 2.0
                    elif hit_sl:
                        raw_r = -1.0
                    else:
                        exit_price = close
                        raw_r = (pos_dir * (exit_price - entry_price)) / atr_entry

                    all_trades.append({
                        "pair": pair,
                        "timeframe": candidate.timeframe,
                        "raw_r": raw_r,
                        "entry_time": row["timestamp"],
                        "direction": pos_dir
                    })
                    in_pos = False

    return all_trades, max(total_days, 1.0)


def run_full_v26_pipeline(days: int = 730, seed: int = 42, output_dir: str = "strategy_research") -> Dict[str, Any]:
    """Runs the complete V26 Research Pipeline."""
    os.makedirs(output_dir, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)

    dataset = load_multi_asset_dataset(days=days, seed=seed)

    # Build candidates
    candidates = [
        MTFTrendPullback("30m"),
        MTFTrendPullback("15m"),
        MTFTrendPullback("1h"),
        BreakoutVolumeExpansion("15m"),
        BreakoutVolumeExpansion("30m"),
        AdaptiveMeanReversion("30m"),
        MomentumContinuation("15m"),
        MomentumContinuation("30m"),
        DynamicRegimeFilter("1h")
    ]

    results = []
    passing_candidates = []

    for c in candidates:
        # Untouched Forward Evaluation (Out-of-Sample 25%)
        fw_trades, fw_days = simulate_candidate_trades(c, dataset, split_key="forward")
        metrics_015 = evaluate_trade_sequence(fw_trades, fw_days, friction_pct=0.0015, risk_per_trade_pct=0.005)
        metrics_030 = evaluate_trade_sequence(fw_trades, fw_days, friction_pct=0.0030, risk_per_trade_pct=0.005)
        metrics_045 = evaluate_trade_sequence(fw_trades, fw_days, friction_pct=0.0045, risk_per_trade_pct=0.005)

        is_passed, verdict = check_statistical_gates(metrics_015)

        # Position Sizing Analysis ONLY IF passed
        risk_sensitivity = {}
        if is_passed:
            risk_sensitivity = evaluate_risk_sizing_sensitivity(fw_trades, fw_days, friction_pct=0.0015)
            passing_candidates.append(c.name)

        res_entry = {
            "candidate_name": c.name,
            "timeframe": c.timeframe,
            "total_trades": metrics_015["total_trades"],
            "trades_per_day": metrics_015["trades_per_day"],
            "win_rate": metrics_015["win_rate"],
            "net_pf_015": metrics_015["net_pf"],
            "net_pf_030": metrics_030["net_pf"],
            "net_pf_045": metrics_045["net_pf"],
            "net_exp_r": metrics_015["net_expectancy_r"],
            "net_exp_usd": metrics_015["net_expectancy_usd"],
            "max_dd_pct": metrics_015["max_drawdown_pct"],
            "ci_lower": metrics_015["bootstrap_ci"][0],
            "ci_upper": metrics_015["bootstrap_ci"][1],
            "verdict": verdict,
            "risk_sensitivity": risk_sensitivity
        }
        results.append(res_entry)

    # Write summary CSV
    csv_path = os.path.join(output_dir, "v26_optimized_expectancy_summary.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "CandidateName", "Timeframe", "TotalTrades", "TradesPerDay", "WinRate%",
            "NetPF_015", "NetPF_030", "NetPF_045", "NetExp_R", "MaxDD%",
            "CILower95", "CIUpper95", "Verdict"
        ])
        for r in results:
            writer.writerow([
                r["candidate_name"], r["timeframe"], r["total_trades"], r["trades_per_day"], r["win_rate"],
                r["net_pf_015"], r["net_pf_030"], r["net_pf_045"], r["net_exp_r"], r["max_dd_pct"],
                r["ci_lower"], r["ci_upper"], r["verdict"]
            ])

    # Write Markdown Report
    report_path = os.path.join(output_dir, "V26_OPTIMIZED_EXPECTANCY_REPORT.md")
    overall_verdict = "REJECTED (NO EDGE PROVEN)" if not passing_candidates else f"QUALIFIED CANDIDATES FOUND ({len(passing_candidates)})"

    with open(report_path, "w") as f:
        f.write("# NEXUS-7 — V26 OPTIMIZED EXPECTANCY RESEARCH REPORT\n\n")
        f.write(f"**Overall Verdict:** `{overall_verdict}`\n\n")
        f.write("## 1. Executive Summary & Objective\n")
        f.write("The V26 research framework evaluated 5 strategy families across 9 liquid crypto pairs and 3 timeframes (15m, 30m, 1h).\n")
        f.write("Rather than forcing an artificial trade-frequency target, V26 focused on discovering a **genuinely profitable 1–2 trades/day strategy**\n")
        f.write("with `Net PF >= 1.25`, `Bootstrap 95% CI Lower Bound > 1.00`, and positive expectancy on untouched out-of-sample data.\n\n")

        f.write("## 2. Out-of-Sample Performance Summary\n\n")
        f.write("| Candidate Name | TF | Trades/Day | Win Rate % | Net PF (0.15%) | Net PF (0.30%) | Net Exp (R) | Max DD % | Bootstrap 95% CI | Verdict |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n")
        for r in results:
            f.write(f"| `{r['candidate_name']}` | `{r['timeframe']}` | **{r['trades_per_day']}** | {r['win_rate']}% | **{r['net_pf_015']}** | {r['net_pf_030']} | **{r['net_exp_r']}R** | {r['max_dd_pct']}% | `[{r['ci_lower']}, {r['ci_upper']}]` | `{r['verdict']}` |\n")

        f.write("\n## 3. Post-Gate Position Sizing Sensitivity (0.5%, 0.75%, 1.0%)\n\n")
        if passing_candidates:
            for r in results:
                if r["risk_sensitivity"]:
                    f.write(f"### Sizing Analysis for `{r['candidate_name']}`\n\n")
                    f.write("| Risk Per Trade | Final Equity ($) | CAGR % | Max DD % | Net PF | Sharpe Ratio |\n")
                    f.write("| :---: | :---: | :---: | :---: | :---: | :---: |\n")
                    for level, metrics in r["risk_sensitivity"].items():
                        f.write(f"| **{level}** | ${metrics['final_equity']} | {metrics['cagr_pct']}% | {metrics['max_drawdown_pct']}% | {metrics['net_pf']} | {metrics['sharpe_ratio']} |\n")
                    f.write("\n")
        else:
            f.write("> **Notice:** No candidates passed the statistical out-of-sample gates (`Net PF >= 1.25` and `Bootstrap CI Lower Bound > 1.00`). Per strict research mandates, position sizing sensitivity was NOT applied to unproven strategies to prevent masking weak edge quality with leverage.\n\n")

        f.write("## 4. Production Safety Mandate\n")
        f.write("- Live real-money trading remains **strictly disabled (`TRADING_ENABLED = False`)**.\n")
        f.write(f"- **Final System Status:** `{overall_verdict}`\n")

    return {
        "overall_verdict": overall_verdict,
        "results": results,
        "passing_candidates": passing_candidates
    }


if __name__ == "__main__":
    res = run_full_v26_pipeline()
    print("V26 Pipeline Execution Complete. Verdict:", res["overall_verdict"])
