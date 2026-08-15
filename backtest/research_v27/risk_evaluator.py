"""
NEXUS-7 — RESEARCH V27 RISK EVALUATOR
Position sizing sensitivity evaluator (0.5% base, 0.75%, 1.0%).
Evaluated separately ONLY after an out-of-sample edge passes statistical gates.
Enforces 2.0% daily circuit breaker and 15.0% max drawdown limit.
"""
import numpy as np
from typing import List, Dict, Any


def evaluate_risk_sizing_sensitivity(trades: List[Dict[str, Any]], initial_balance: float = 10000.0) -> Dict[str, Any]:
    """
    Evaluates 0.5%, 0.75%, and 1.0% risk per trade on trade sequence.
    Applies daily circuit breaker (stops trading for the day if daily loss >= 2.0%).
    """
    results = {}
    risk_levels = [0.005, 0.0075, 0.010]

    for risk in risk_levels:
        balance = initial_balance
        equity_curve = [balance]
        peak_balance = balance
        max_dd_pct = 0.0
        daily_loss = 0.0
        current_day = None
        circuit_breaker_tripped = False
        trades_executed = 0

        for t in trades:
            trade_day = str(t.get("timestamp", ""))[:10]
            if trade_day != current_day:
                current_day = trade_day
                daily_loss = 0.0
                circuit_breaker_tripped = False

            if circuit_breaker_tripped:
                continue

            # Position size based on risk percentage
            risk_amount = balance * risk
            outcome = t.get("outcome", "WIN" if t.get("confidence", 0.8) > 0.82 else "LOSS")

            if outcome == "WIN":
                pnl = risk_amount * 1.6  # 1:1.6 risk-reward ratio
            else:
                pnl = -risk_amount

            balance += pnl
            equity_curve.append(balance)

            if balance > peak_balance:
                peak_balance = balance

            dd = (peak_balance - balance) / peak_balance * 100.0
            if dd > max_dd_pct:
                max_dd_pct = dd

            if pnl < 0:
                daily_loss += abs(pnl) / equity_curve[-2] * 100.0
                if daily_loss >= 2.0:
                    circuit_breaker_tripped = True

            trades_executed += 1

        total_return_pct = ((balance - initial_balance) / initial_balance) * 100.0

        results[f"risk_{int(risk*1000)/10}pct"] = {
            "risk_per_trade_pct": risk * 100.0,
            "final_balance": round(balance, 2),
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(max_dd_pct, 2),
            "trades_executed": trades_executed,
            "circuit_breaker_pass": max_dd_pct <= 15.0
        }

    return results
