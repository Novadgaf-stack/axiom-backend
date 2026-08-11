"""
NEXUS-7 — OPERATIONAL CHAOS & DISRUPTION CERTIFICATION TEST SUITE (PHASE 3)
Tests live operational disruption scenarios while connected to verify safe recovery
without state loss, risk limit bypass, duplicate orders, or unhandled positions.
"""
import time
import pytest
from app.state_machine import TradingStateMachine, EngineState
from app.kill_switch import EmergencyKillSwitch
from app.startup_check import StartupSafetyChecker
from app.reconciliation import StateReconciler
from app.watchdog import ServiceWatchdog
from app.order_idempotency import generate_client_order_id, OrderIdempotencyManager
from app.risk import RiskManager
from app.testnet_runner import TestnetExecutionRunner


def test_scenario_1_engine_restart_with_open_position():
    """Bot restarts while a position is open -> Restores state without creating duplicate order."""
    runner = TestnetExecutionRunner()
    
    # 1. Execute initial trade
    pos = runner.execute_testnet_signal("BTCUSDT", 50000.0, 1000.0, "BUY", 95, 1)
    assert pos is not None
    assert "BTCUSDT" in runner.active_positions
    
    # 2. Simulate bot crash/restart: Create new runner, run startup safety check & reconciliation
    runner_restarted = TestnetExecutionRunner()
    checker = StartupSafetyChecker(runner_restarted.state_machine)
    checker.run_all_checks(environment="TESTNET", live_trading_enabled=False)
    
    # Reconcile against exchange venue state
    ex_positions = {"BTCUSDT": pos["quantity"]}
    ex_orders = list(runner.active_orders.keys())
    rec_res = runner_restarted.run_reconciliation_check(ex_positions, ex_orders)
    
    assert rec_res["status"] == "SYNCED"
    assert runner_restarted.duplicate_orders_count == 0


def test_scenario_2_network_websocket_disconnect_and_reconnect():
    """Network/WebSocket feed disconnects -> Watchdog degrades state; reconnect restores."""
    sm = TradingStateMachine(initial_state=EngineState.TRADING)
    watchdog = ServiceWatchdog(sm, stale_threshold_sec=0.05)
    
    time.sleep(0.08)
    health = watchdog.check_health()
    assert not health["is_healthy"]
    assert sm.current_state == EngineState.DEGRADED
    
    # Reconnect & record heartbeat
    watchdog.record_heartbeat("market_data")
    watchdog.record_heartbeat("exchange_api")
    watchdog.record_heartbeat("strategy_engine")
    watchdog.record_heartbeat("risk_engine")
    watchdog.record_heartbeat("database")
    
    health_recovered = watchdog.check_health()
    assert health_recovered["is_healthy"]
    sm.transition_to(EngineState.HEALTH_CHECK, reason="Heartbeat restored")
    sm.transition_to(EngineState.READY, reason="Health check passed after reconnect")
    sm.transition_to(EngineState.TRADING, reason="Ready to trade after reconnect")
    assert sm.current_state == EngineState.TRADING


def test_scenario_3_order_timeout_during_submission():
    """Order submission times out -> Queries venue first without blindly retrying."""
    runner = TestnetExecutionRunner()
    cid = generate_client_order_id("BTCUSDT", "buy", 10, 1700000000)
    runner.idempotency_mgr.register_order(cid, "BTCUSDT", "buy", 50000.0, 0.1)
    
    # Venue confirms order exists -> NO_RETRY
    res_exists = runner.idempotency_mgr.handle_timeout(cid, lambda id_: {"exists": True, "status": "FILLED"})
    assert res_exists["action"] == "NO_RETRY"
    assert res_exists["status"] == "FILLED"


def test_scenario_4_external_venue_order_cancellation():
    """Order canceled externally on exchange -> Reconciliation detects mismatch and halts."""
    sm = TradingStateMachine(initial_state=EngineState.TRADING)
    reconciler = StateReconciler(sm)
    
    local_positions = {"BTCUSDT": 1.0}
    exchange_positions = {"BTCUSDT": 0.0}  # Canceled/closed on venue
    
    res = reconciler.reconcile(local_positions, exchange_positions, ["ord_1"], [])
    assert not res["is_synced"]
    assert res["status"] == "STATE_MISMATCH"
    assert sm.current_state == EngineState.RECONCILING


def test_scenario_5_restart_after_unresolved_order():
    """Restart after unresolved order -> Idempotency & startup check resolves state."""
    mgr = OrderIdempotencyManager()
    cid = generate_client_order_id("SOLUSDT", "buy", 50, 1700000500)
    mgr.register_order(cid, "SOLUSDT", "buy", 150.0, 10.0)
    
    res = mgr.handle_timeout(cid, lambda id_: {"exists": False})
    assert res["action"] == "SAFE_TO_CANCEL_OR_RETRY"
    assert res["status"] == "NOT_ON_VENUE"


def test_scenario_6_daily_loss_limit_breach():
    """Realized daily loss reaches limit -> Central Risk Engine blocks new orders."""
    rm = RiskManager()
    rm.bootstrap_daily_state(day_start_equity=10000.0, realized_pnl_today=-350.0)  # -3.5% loss (> 3.0% max_daily_loss_pct)
    
    # Try order risk validation -> Rejected
    ok, reason, plan = rm.validate_order_risk("BTCUSDT", "buy", 50000.0, 1000.0, 10000.0, 0, trading_allowed=True)
    assert not ok
    assert reason == "DAILY_LOSS_LIMIT_REACHED"
    assert reason == "DAILY_LOSS_LIMIT_REACHED"


def test_scenario_7_max_open_positions_limit_breach():
    """Max open positions limit reached -> Additional orders rejected."""
    runner = TestnetExecutionRunner()
    
    # Fill up 3 positions
    runner.execute_testnet_signal("BTCUSDT", 50000.0, 1000.0, "BUY", 95, 1)
    runner.execute_testnet_signal("ETHUSDT", 3000.0, 100.0, "BUY", 95, 2)
    runner.execute_testnet_signal("SOLUSDT", 150.0, 5.0, "BUY", 95, 3)
    
    assert len(runner.active_positions) == 3
    
    # 4th trade -> Rejected by Risk Engine
    pos_4 = runner.execute_testnet_signal("BNBUSDT", 500.0, 10.0, "BUY", 95, 4)
    assert pos_4 is None
    assert len(runner.active_positions) == 3


def test_scenario_8_emergency_kill_switch_during_trading():
    """Emergency Kill Switch triggered during trading -> Halts engine immediately."""
    runner = TestnetExecutionRunner()
    assert runner.state_machine.can_trade()
    
    ks = EmergencyKillSwitch(runner.state_machine)
    res = ks.trigger_emergency_stop("Chaos Test Kill Switch Trigger")
    
    assert ks.is_halted
    assert runner.state_machine.current_state == EngineState.HALTED
    assert not runner.state_machine.can_trade()
    
    # Try order after kill switch -> Blocked
    pos = runner.execute_testnet_signal("BTCUSDT", 50000.0, 1000.0, "BUY", 95, 5)
    assert pos is None
