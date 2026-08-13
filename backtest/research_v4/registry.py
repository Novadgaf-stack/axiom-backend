"""
NEXUS-7 — IMMUTABLE EXPERIMENT REGISTRY (RESEARCH V4)
Hashes and records every strategy hypothesis experiment into research_v4_experiments.jsonl.
"""
import hashlib
import json
import os
import time
from typing import Dict


class ExperimentRegistry:
    """Logs immutable experiment hashes to prevent rediscovering failed parameter spaces."""

    def __init__(self, registry_path: str = "research_v4_experiments.jsonl"):
        self.registry_path = registry_path

    def _generate_experiment_hash(self, experiment_data: Dict) -> str:
        param_str = json.dumps(experiment_data.get("parameters", {}), sort_keys=True)
        raw = f"{experiment_data.get('hypothesis_name', '')}:{param_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def is_experiment_logged(self, exp_hash: str) -> bool:
        if not os.path.exists(self.registry_path):
            return False
        with open(self.registry_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if record.get("hash") == exp_hash:
                            return True
                    except Exception:
                        pass
        return False

    def log_experiment(self, experiment_name: str, hypothesis_name: str, parameters: Dict, results: Dict) -> str:
        record = {
            "timestamp": time.time(),
            "experiment_name": experiment_name,
            "hypothesis_name": hypothesis_name,
            "parameters": parameters,
            "results": results,
        }
        exp_hash = self._generate_experiment_hash(record)
        record["hash"] = exp_hash

        with open(self.registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        return exp_hash
