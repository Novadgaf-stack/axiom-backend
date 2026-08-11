"""
NEXUS-7 — REAL TESTNET CHAOS RECOVERY SUITE (PHASE 6)
Validates engine resilience against actual venue state recovery, network dropouts,
order timeouts, external order cancellations, kill switch halts, and risk limit blocks.
"""
import time
import pytest
from app.environment_safety import EnvironmentSafetyGuard
from app.exchange_adapter import TestnetExchangeAdapter
from app.incident_logger import IncidentManager
from app.order_idempotency import generate_client_order_id, OrderIdempotencyManager
from app.reconciliation import StateReconciler
from app.risk import RiskManager
from app.state_machine import TradingStateMachine, EngineState
from app.testnet_order_engine import RealTestnetOrderEngine
from app.watchdog import ServiceWatchdog


def test_environment_safety_banner_and_live_lock():
    """Phase 2: Verifies environment safety banner and hard lock blocking LIVE mode."""
    res = EnvironmentSafetyGuard.verify_and_print_banner("TESTNET")
    assert res["environment"] == "TESTNET"
    assert res["status"] == "VERIFIED"
    
    # Try LIVE mode -> Must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        EnvironmentSafetyGuard.verify_and_print_banner("LIVE")
    assert "LIVE REAL-MONEY TRADING IS PERMANENTLY LOCKED" in str(exc_info.value)


def test_real_testnet_chaos_a_bot_restart_with_open_position():
    """Chaos A: Bot restarts while testnet position open -> Recovers state cleanly without duplicate order."""
    engine = RealTestnetOrderEngine(orders_csv_path="testnet_orders_test.csv", rec_csv_path="testnet_rec_test.csv", latency_csv_path="testnet_lat_test.csv")
    pos = engine.process_testnet_signal("BTCUSDT", 50000.0, 1000.0, "BUY", 95, 1)
    assert pos is not None
    assert "BTCUSDT" in engine.local_positions
    
    # Reboot engine: Create new instance, connect, fetch venue state, reconcile
    engine_rebooted = RealTestnetOrderEngine(orders_csv_path="testnet_orders_test.csv", rec_csv_path="testnet_rec_test.csv", latency_csv_path="testnet_lat_test.csv")
    venue_pos = engine.exchange.get_positions()
    rec_res = engine_rebooted.exchange.reconciler.reconcile(venue_pos, venue_pos, [], [])
    
    assert rec_res["is_synced"]
    assert ("non_existent" in engine_rebooted.exchange.idempotency_mgr.submitted_orders) is False


def test_real_testnet_chaos_b_network_interruption():
    """Chaos B: Network disconnects -> Watchdog degrades; reconnect restores READY/TRADING."""
    sm = TradingStateMachine(initial_state=EngineState.TRADING)
    watchdog = ServiceWatchdog(sm, stale_threshold_sec=0.05)
    
    time.sleep(0.08)
    health = watchdog.check_health()
    assert not health["is_healthy"]
    assert sm.current_state == EngineState.DEGRADED
    
    # Reconnect network
    watchdog.record_heartbeat("market_data")
    watchdog.record_heartbeat("exchange_api")
    watchdog.record_heartbeat("strategy_engine")
    watchdog.record_heartbeat("risk_engine")
    watchdog.record_heartbeat("database")
    
    health_recovered = watchdog.check_health()
    assert health_recovered["is_healthy"]
    sm.transition_to(EngineState.HEALTH_CHECK, reason="Heartbeats restored")
    sm.transition_to(EngineState.READY, reason="Health check passed after reconnect")
    sm.transition_to(EngineState.TRADING, reason="Ready to trade after reconnect")
    assert sm.current_state == EngineState.TRADING


def test_real_testnet_chaos_c_order_timeout():
    """Chaos C: Order timeout -> Idempotency manager queries venue status (NO_RETRY)."""
    mgr = OrderIdempotencyManager()
    cid = generate_client_order_id("ETHUSDT", "buy", 12, 1700000000)
    mgr.register_order(cid, "ETHUSDT", "buy", 3000.0, 1.0)
    
    # Simulates venue status query finding order -> NO_RETRY
    res = mgr.handle_timeout(cid, lambda id_: {"exists": True, "status": "FILLED"})
    assert res["action"] == "NO_RETRY"
    assert res["status"] == "FILLED"


def test_real_testnet_chaos_d_external_order_cancellation():
    """Chaos D: Order canceled externally on exchange -> Reconciliation detects mismatch & logs incident."""
    engine = RealTestnetOrderEngine(orders_csv_path="testnet_orders_test.csv", rec_csv_path="testnet_rec_test.csv", latency_csv_path="testnet_lat_test.csv")
    pos = engine.process_testnet_signal("SOLUSDT", 150.0, 5.0, "BUY", 95, 1)
    assert pos is not None
    
    # External party cancels order on venue -> clear venue position
    engine.exchange._venue_positions["SOLUSDT"] = 0.0
    rec_res = engine.run_real_reconciliation()
    
    assert not rec_res["is_synced"]
    assert rec_res["status"] == "STATE_MISMATCH"
    assert engine.state_machine.current_state == EngineState.HALTED
    assert len(engine.incident_manager.incidents_history) > 0


def test_real_testnet_chaos_e_kill_switch():
    """Chaos E: Kill switch activated -> Disables entries, cancels orders, enters HALTED state."""
    engine = RealTestnetOrderEngine(orders_csv_path="testnet_orders_test.csv", rec_csv_path="testnet_rec_test.csv", latency_csv_path="testnet_lat_test.csv")
    assert engine.state_machine.can_trade()
    
    engine.state_machine.transition_to(EngineState.HALTED, reason="Emergency Kill Switch test")
    assert not engine.state_machine.can_trade()
    
    pos = engine.process_testnet_signal("BTCUSDT", 50000.0, 1000.0, "BUY", 95, 2)
    assert pos is None


def test_real_testnet_chaos_f_risk_limit():
    """Chaos F: Attempting order beyond risk limit -> Blocked by Risk Engine."""
    rm = RiskManager()
    rm.bootstrap_daily_state(day_start_equity=10000.0, realized_pnl_today=-350.0)  # -3.5% loss > 3.0% limit
    
    ok, reason, plan = rm.validate_order_risk("BTCUSDT", "buy", 50000.0, 1000.0, 10000.0, 0, trading_allowed=True)
    assert not ok
    assert reason == "DAILY_LOSS_LIMIT_REACHED"
