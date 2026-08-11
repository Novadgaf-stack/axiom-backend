"""
NEXUS-7 — RESEARCH V3 ENGINE AUDIT & SIGNAL FINGERPRINTING
Fixes 0-signal audit classification: strategies with 0 observations are classified
as 'INSUFFICIENT DATA', not 'PASSED (Independent)'.
"""
import os
import pandas as pd
import numpy as np


def compute_jaccard_overlap(s1: pd.Series, s2: pd.Series) -> float:
    """Computes Jaccard Similarity index between two binary signal series."""
    b1 = (s1 != 0).astype(int)
    b2 = (s2 != 0).astype(int)
    intersection = (b1 & b2).sum()
    union = (b1 | b2).sum()
    if union == 0:
        return 0.0
    return float(intersection / union)


def run_engine_audit_v3(universe_candles: dict[str, list[dict]], strategies: list) -> tuple[pd.DataFrame, str]:
    """
    Audits signal independence across V3 strategy families.
    Returns (fingerprint_df, markdown_report_text).
    """
    # Pick benchmark asset (BTCUSDT if available, else first pair)
    pair = "BTCUSDT" if "BTCUSDT" in universe_candles else list(universe_candles.keys())[0]
    candles = universe_candles[pair]
    if candles and isinstance(candles[0], (list, tuple)):
        df = pd.DataFrame(candles, columns=["ts", "open", "high", "low", "close", "volume"])
    else:
        df = pd.DataFrame(candles)
    
    records = []
    signal_vectors = {}
    
    for strat in strategies:
        sig_series = strat.generate_signals(df, symbol=pair)
        signal_vectors[strat.exp_id] = sig_series
        
        total_sigs = int((sig_series != 0).sum())
        long_sigs = int((sig_series == 1).sum())
        short_sigs = int((sig_series == -1).sum())
        
        # Calculate unique signal timestamps
        unique_ts = len(df.iloc[sig_series[sig_series != 0].index]["ts"].unique()) if total_sigs > 0 else 0
        
        records.append({
            "exp_id": strat.exp_id,
            "strategy_name": strat.name,
            "total_signals": total_sigs,
            "unique_timestamps": unique_ts,
            "long_signals": long_sigs,
            "short_signals": short_sigs,
            "max_pairwise_overlap_pct": 0.0,
            "uniqueness_verdict": "PENDING"
        })
        
    df_results = pd.DataFrame(records)
    
    # Compute pairwise overlaps and assign correct verdicts
    for i, row1 in df_results.iterrows():
        exp1 = row1["exp_id"]
        v1 = signal_vectors[exp1]
        max_overlap = 0.0
        
        for j, row2 in df_results.iterrows():
            if i == j:
                continue
            exp2 = row2["exp_id"]
            v2 = signal_vectors[exp2]
            overlap = compute_jaccard_overlap(v1, v2)
            if overlap > max_overlap:
                max_overlap = overlap
                
        df_results.at[i, "max_pairwise_overlap_pct"] = round(max_overlap * 100.0, 2)
        
        # FIX: Zero-signal strategies MUST be classified as INSUFFICIENT DATA
        if row1["total_signals"] == 0:
            df_results.at[i, "uniqueness_verdict"] = "INSUFFICIENT DATA"
        elif max_overlap > 0.95:
            df_results.at[i, "uniqueness_verdict"] = "REJECTED (Collision)"
        else:
            df_results.at[i, "uniqueness_verdict"] = "PASSED (Independent)"
            
    # Format Markdown Report
    lines = [
        "# NEXUS-7 — RESEARCH V3 ENGINE AUDIT REPORT",
        "",
        "## Signal Fingerprints & Independence Verification",
        "",
        "| Exp ID | Strategy Candidate Name | Total Signals | Unique Timestamps | Long Signals | Short Signals | Max Pairwise Overlap % | Uniqueness Verdict |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |"
    ]
    
    for _, r in df_results.iterrows():
        lines.append(
            f"| **{r['exp_id']}** | {r['strategy_name']} | {r['total_signals']} | {r['unique_timestamps']} | "
            f"{r['long_signals']} | {r['short_signals']} | {r['max_pairwise_overlap_pct']}% | **{r['uniqueness_verdict']}** |"
        )
        
    lines.append("")
    report_md = "\n".join(lines)
    
    return df_results, report_md
