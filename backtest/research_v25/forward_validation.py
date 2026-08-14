"""
NEXUS-7 — RESEARCH V25 FORWARD VALIDATION WRAPPER
Orchestrates the complete V25 research pipeline.
"""
from backtest.research_v25.engine import run_full_v25_pipeline

if __name__ == "__main__":
    res = run_full_v25_pipeline()
    print("V25 Forward Validation Complete. Verdict:", res["overall_verdict"])
