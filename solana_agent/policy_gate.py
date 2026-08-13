"""
Deterministic Policy & Risk Gate for Solana Agent Layer.
Validates decision context BEFORE signing or broadcasting to Solana Devnet.
"""
import time
from typing import List
from solana_agent.config import solana_settings
from solana_agent.schemas import PolicyCheckResult


class SolanaPolicyGate:
    def __init__(self):
        self._tx_timestamps: List[float] = []

    def _purge_old_timestamps(self):
        now = time.time()
        one_hour_ago = now - 3600
        self._tx_timestamps = [ts for ts in self._tx_timestamps if ts > one_hour_ago]

    def evaluate_policy(self, sol_amount: float, confidence_score: float) -> PolicyCheckResult:
        self._purge_old_timestamps()

        sol_cap_valid = sol_amount <= solana_settings.max_sol_per_tx
        confidence_valid = confidence_score >= solana_settings.min_confidence_floor
        rate_limit_valid = len(self._tx_timestamps) < solana_settings.max_tx_per_hour

        reasons = []
        if not sol_cap_valid:
            reasons.append(f"sol_amount ({sol_amount}) exceeds max_sol_per_tx ({solana_settings.max_sol_per_tx})")
        if not confidence_valid:
            reasons.append(f"confidence_score ({confidence_score}) below floor ({solana_settings.min_confidence_floor})")
        if not rate_limit_valid:
            reasons.append(f"hourly_rate_limit_exceeded ({len(self._tx_timestamps)}/{solana_settings.max_tx_per_hour})")

        passed = sol_cap_valid and confidence_valid and rate_limit_valid
        rejection_reason = " | ".join(reasons) if not passed else None

        return PolicyCheckResult(
            passed=passed,
            sol_cap_valid=sol_cap_valid,
            rate_limit_valid=rate_limit_valid,
            confidence_valid=confidence_valid,
            rejection_reason=rejection_reason,
        )

    def record_execution(self):
        self._tx_timestamps.append(time.time())


policy_gate = SolanaPolicyGate()
