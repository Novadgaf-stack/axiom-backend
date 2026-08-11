"""
NEXUS-7 — ENVIRONMENT SAFETY & PRODUCTION HARD LOCK (PHASE 2)
Verifies environment settings on process startup, prints mandatory security banner,
and strictly blocks process startup if ENVIRONMENT=LIVE or LIVE_TRADING=true.
"""
import os
import sys
from typing import Dict
from app.logging_setup import get_logger

logger = get_logger("environment_safety")


class EnvironmentSafetyGuard:
    """Enforces environment isolation and live trading hard locks."""
    
    @staticmethod
    def verify_and_print_banner(
        environment: str = "TESTNET",
        exchange_id: str = "binance_testnet",
        symbol: str = "BTC/USDT"
    ) -> Dict[str, str]:
        """
        Validates environment configuration on startup and prints mandatory status banner.
        Refuses process startup if ENVIRONMENT=LIVE.
        """
        env_upper = (os.getenv("ENVIRONMENT") or environment).upper()
        live_flag = os.getenv("LIVE_TRADING", "false").lower() in ("true", "1", "yes")
        
        banner_lines = [
            "=" * 44,
            "NEXUS-7 TRADING ENVIRONMENT",
            "=" * 44,
            f"ENVIRONMENT: {env_upper}",
            f"LIVE TRADING: {'ENABLED (HARD LOCKED)' if live_flag else 'DISABLED'}",
            f"EXCHANGE: {exchange_id.upper()}",
            f"SYMBOL: {symbol}",
            "=" * 44,
        ]
        
        banner_text = "\n".join(banner_lines)
        print(banner_text)
        
        # Mandatory Hard Lock Guard
        if env_upper == "LIVE" or live_flag:
            error_msg = (
                "FATAL SAFETY BLOCK: ENVIRONMENT=LIVE OR LIVE_TRADING=true DETECTED. "
                "LIVE REAL-MONEY TRADING IS PERMANENTLY LOCKED BECAUSE QUANTITATIVE EDGE IS NOT PROVEN. "
                "PROCESS TERMINATED IMMEDIATELY."
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
            
        logger.info(f"Environment verification passed cleanly: {env_upper} (Live trading locked).")
        return {
            "environment": env_upper,
            "live_trading": "DISABLED",
            "exchange": exchange_id,
            "symbol": symbol,
            "status": "VERIFIED"
        }
