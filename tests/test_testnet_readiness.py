"""
NEXUS-7 — TESTNET READINESS & FAILURE INJECTION TEST SUITE
Tests operational state machine, emergency kill switch, 13-step startup safety, central risk gatekeeper,
exchange reconciliation, watchdog, order idempotency, audit logging, and live trading hard lock.
"""
import os
import time
import pytest
from app.state_machine import TradingStateMachine, EngineState
from app.kill_switch import EmergencyKillSwitch
from app.startup_check import StartupSafetyChecker
from app.reconciliation import StateReconciler
from app.watchdog import ServiceWatchdog
from app.order_idempotency import generate_client_order_id, OrderIdempotencyManager
from app.audit_log import ImmutableAuditLogger
from app.shadow_mode import ShadowModeEngine
from app.risk import RiskManager, TradePlan


def test_state_machine_valid_and_invalid_transitions():
    sm = TradingStateMachine(initial_state=EngineState.STARTING)
    assert sm.current_state == EngineState.STARTING
    assert not sm.can_trade()
    
    # Valid transitions: STARTING -> HEALTH_CHECK -> READY -> TRADING
    assert sm.transition_to(EngineState.HEALTH_CHECK, reason="Test startup")
    assert sm.transition_to(EngineState.READY, reason="Health check pass")
    assert sm.transition_to(EngineState.TRADING, reason="Start trading")
    assert sm.can_trade()
    
    # Invalid transition: TRADING directly to STARTING is invalid
    assert not sm.transition_to(EngineState.STARTING, reason="Invalid jump")
    assert sm.current_state == EngineState.TRADING


def test_emergency_kill_switch():
    sm = TradingStateMachine(initial_state=EngineState.TRADING)
    ks = EmergencyKillSwitch(sm)
    
    assert not ks.is_halted
    res = ks.trigger_emergency_stop("API Test Emergency Stop")
    
    assert ks.is_halted
    assert res["status"] == "HALTED"
    assert sm.current_state == EngineState.HALTED
    assert not sm.can_trade()
    
    # Reset
    reset_res = ks.manual_reset(reset_by="test_admin")
    assert not ks.is_halted
    assert sm.current_state == EngineState.HEALTH_CHECK


def test_startup_safety_procedure_and_live_lock():
    sm = TradingStateMachine(initial_state=EngineState.STARTING)
    checker = StartupSafetyChecker(sm)
    
    # Testnet environment -> Passed
    passed, results = checker.run_all_checks(environment="TESTNET", live_trading_enabled=False)
    assert passed
    assert sm.current_state == EngineState.READY
    
    # Live environment with trading enabled -> BLOCKED by Live Hard Lock
    sm2 = TradingStateMachine(initial_state=EngineState.STARTING)
    checker2 = StartupSafetyChecker(sm2)
    passed_live, results_live = checker2.run_all_checks(environment="LIVE", live_trading_enabled=True)
    assert not passed_live
    assert sm2.current_state == EngineState.HALTED


def test_central_risk_gatekeeper():
    rm = RiskManager()
    
    # 1. Trading halted -> Rejected
    ok, reason, plan = rm.validate_order_risk("BTCUSDT", "buy", 50000.0, 1000.0, 10000.0, 0, trading_allowed=False)
    assert not ok
    assert reason == "TRADING_HALTED_OR_DISABLED"
    
    # 2. Max open positions reached -> Rejected
    ok_pos, reason_pos, plan_pos = rm.validate_order_risk("BTCUSDT", "buy", 50000.0, 1000.0, 10000.0, 10, trading_allowed=True)
    assert not ok_pos
    assert reason_pos == "TRADE_PLAN_REJECTED_BY_RISK_LIMITS"
    
    # 3. Valid parameters -> Approved
    ok_valid, reason_valid, plan_valid = rm.validate_order_risk("BTCUSDT", "buy", 50000.0, 1000.0, 10000.0, 0, trading_allowed=True)
    assert ok_valid
    assert reason_valid is None
    assert isinstance(plan_valid, TradePlan)


def test_exchange_reconciliation_mismatch():
    sm = TradingStateMachine(initial_state=EngineState.TRADING)
    reconciler = StateReconciler(sm)
    
    local_pos = {"BTCUSDT": 1.5, "ETHUSDT": 10.0}
    ex_pos = {"BTCUSDT": 1.5, "ETHUSDT": 8.0}  # Mismatch on ETH
    
    res = reconciler.reconcile(local_pos, ex_pos, ["ord_1"], ["ord_1"])
    assert not res["is_synced"]
    assert res["status"] == "STATE_MISMATCH"
    assert sm.current_state == EngineState.RECONCILING


def test_watchdog_heartbeat_staleness():
    sm = TradingStateMachine(initial_state=EngineState.TRADING)
    watchdog = ServiceWatchdog(sm, stale_threshold_sec=0.1)
    
    # Sleep to make heartbeats stale
    time.sleep(0.15)
    
    health = watchdog.check_health()
    assert not health["is_healthy"]
    assert len(health["stale_services"]) > 0
    assert sm.current_state == EngineState.DEGRADED


def test_order_idempotency_and_timeout():
    cid = generate_client_order_id("BTCUSDT", "buy", 100, 1700000000)
    assert cid.startswith("n7_btcusdt_buy_100_")
    
    mgr = OrderIdempotencyManager()
    mgr.register_order(cid, "BTCUSDT", "buy", 50000.0, 0.1)
    
    # Timeout handler querying venue status (Venue confirms order exists)
    res_exists = mgr.handle_timeout(cid, lambda id_: {"exists": True, "status": "FILLED", "order_id": "v_123"})
    assert res_exists["action"] == "NO_RETRY"
    assert res_exists["status"] == "FILLED"
    
    # Timeout handler querying venue status (Venue confirms order does NOT exist)
    cid2 = generate_client_order_id("ETHUSDT", "buy", 101, 1700000005)
    mgr.register_order(cid2, "ETHUSDT", "buy", 3000.0, 1.0)
    res_not_exists = mgr.handle_timeout(cid2, lambda id_: {"exists": False})
    assert res_not_exists["action"] == "SAFE_TO_CANCEL_OR_RETRY"


def test_immutable_audit_logger(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    logger = ImmutableAuditLogger(log_path=str(log_file), environment="TESTNET")
    
    rec = logger.log_event("TEST_EVENT", "BTCUSDT", {"key": "val"})
    assert rec["environment"] == "TESTNET"
    assert rec["event_type"] == "TEST_EVENT"
    assert os.path.exists(log_file)


def test_shadow_mode(tmp_path):
    log_file = tmp_path / "shadow_audit.jsonl"
    audit_logger = ImmutableAuditLogger(log_path=str(log_file), environment="SHADOW")
    shadow = ShadowModeEngine(audit_logger)
    
    rec = shadow.evaluate_shadow_trade("BTCUSDT", "buy", 50000.0, 0.1, 48000.0, 55000.0, "Test Signal")
    assert rec["status"] == "HYPOTHETICAL_FILLED"
    assert rec["environment"] == "SHADOW"
    assert len(shadow.hypothetical_positions) == 1
