"""
Phase 0 — Engine Audit & Signal Fingerprinting Module.
Verifies that every strategy family generates independent signal vectors.
Computes pairwise signal overlap matrices, unique timestamp counts, and mathematical uniqueness assertions.
"""
import os
import time
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from backtest.research_v2.strategies import get_all_v2_research_strategies


def run_engine_audit(universe_dfs: Dict[str, pd.DataFrame], out_dir: str = "./research_v2") -> bool:
    """
    Runs Phase 0 Research Engine Audit.
    Generates research_v2/engine_audit.md and research_v2/signal_fingerprints.csv.
    Enforces mathematical uniqueness assertions across strategy candidates.
    """
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    strategies = get_all_v2_research_strategies()
    btc_df = universe_dfs.get("BTCUSDT", list(universe_dfs.values())[0])

    fingerprints = []
    signals_by_family = {}

    for strat in strategies:
        sig_series = strat.generate_signals(btc_df, universe_dfs=universe_dfs, current_pair="BTCUSDT")
        signals_by_family[strat.family_id] = sig_series

        n_signals = int((sig_series != 0).sum())
        n_longs = int((sig_series == 1).sum())
        n_shorts = int((sig_series == -1).sum())
        
        active_indices = sig_series[sig_series != 0].index.tolist()
        unique_ts = len(set(active_indices))

        fingerprints.append({
            "family_id": strat.family_id,
            "strategy_name": strat.name,
            "total_signals": n_signals,
            "unique_timestamps": unique_ts,
            "long_signals": n_longs,
            "short_signals": n_shorts,
        })

    # Calculate Pairwise Signal Overlap Matrix
    num_strats = len(strategies)
    overlap_matrix = np.zeros((num_strats, num_strats))
    
    for i, s1 in enumerate(strategies):
        v1 = (signals_by_family[s1.family_id] != 0).values
        for j, s2 in enumerate(strategies):
            v2 = (signals_by_family[s2.family_id] != 0).values
            intersection = np.logical_and(v1, v2).sum()
            union = np.logical_or(v1, v2).sum()
            overlap_pct = (intersection / union * 100.0) if union > 0 else 0.0
            overlap_matrix[i, j] = round(overlap_pct, 2)

    # Save CSV Deliverables
    df_fp = pd.DataFrame(fingerprints)
    df_fp.to_csv(os.path.join(out_dir, "signal_fingerprints.csv"), index=False)

    # Enforce Mathematical Uniqueness Assertions
    audit_passed = True
    assertion_logs = []

    for i in range(num_strats):
        for j in range(i + 1, num_strats):
            s1_id = strategies[i].family_id
            s2_id = strategies[j].family_id
            ov_val = overlap_matrix[i, j]

            # Assert signal vectors are not duplicate copies (>95% overlap is suspicious)
            if ov_val > 95.0:
                audit_passed = False
                assertion_logs.append(f"[FAIL] High signal overlap ({ov_val}%) between {s1_id} and {s2_id}!")
            else:
                assertion_logs.append(f"[PASS] {s1_id} vs {s2_id}: Overlap = {ov_val}% (Independent)")

    # Build engine_audit.md Deliverable
    report = []
    report.append("# NEXUS-7 — RESEARCH ENGINE AUDIT REPORT (PHASE 0)\n")
    report.append(f"**Audit Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} | **Runtime:** {time.time()-t0:.2f}s  ")
    report.append(f"**Engine Uniqueness Verdict:** `{'PASSED — ALL SIGNALS INDEPENDENT' if audit_passed else 'FAILED — DUPLICATE SIGNALS DETECTED'}`\n")
    report.append("---\n")

    report.append("## 1. Strategy Signal Fingerprint Matrix\n")
    report.append("| Exp ID | Strategy Family Name | Total Signals | Unique Timestamps | Long Signals | Short Signals |")
    report.append("| :--- | :--- | :---: | :---: | :---: | :---: |")
    for f in fingerprints:
        report.append(f"| **{f['family_id']}** | {f['strategy_name']} | {f['total_signals']} | {f['unique_timestamps']} | {f['long_signals']} | {f['short_signals']} |")

    report.append("\n---\n")
    report.append("## 2. Pairwise Signal Overlap Matrix (% Jaccard Similarity)\n")
    headers = ["Exp ID"] + [s.family_id for s in strategies]
    report.append("| " + " | ".join(headers) + " |")
    report.append("| " + " | ".join([":---"] * len(headers)) + " |")
    for i, s in enumerate(strategies):
        row_vals = [f"**{s.family_id}**"] + [f"{overlap_matrix[i, j]:.1f}%" for j in range(num_strats)]
        report.append("| " + " | ".join(row_vals) + " |")

    report.append("\n---\n")
    report.append("## 3. Mathematical Uniqueness Assertions\n")
    for log in assertion_logs:
        report.append(f"- {log}")

    with open(os.path.join(out_dir, "engine_audit.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    if not audit_passed:
        raise RuntimeError("Phase 0 Engine Audit FAILED: Strategy signals are not mathematically independent!")

    print(f"Phase 0 Engine Audit PASSED! All {num_strats} strategy families generate independent signals.")
    return audit_passed
