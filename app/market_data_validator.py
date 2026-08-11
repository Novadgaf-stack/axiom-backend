"""
NEXUS-7 — MARKET DATA VALIDATOR & LATENCY TRACKER (PHASE 3)
Inspects incoming testnet candles for timestamp integrity, ordering, duplicates,
staleness, price bounds, and latency metrics. Rejects malformed data.
"""
import time
from typing import Dict, List, Optional, Tuple
from app.logging_setup import get_logger

logger = get_logger("market_data_validator")


class MarketDataValidator:
    """Validates real/testnet market data feed quality and measures latency."""
    def __init__(self, max_staleness_sec: float = 15.0):
        self.max_staleness_sec = max_staleness_sec
        self.last_timestamps: Dict[str, float] = {}
        self.latency_records: List[Dict] = []
        self.rejected_candles_count = 0
        self.valid_candles_count = 0

    def validate_bar(
        self,
        symbol: str,
        open_time_ms: int,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        timeframe: str = "15m"
    ) -> Tuple[bool, Optional[str], float]:
        """
        Validates bar data and measures latency.
        Returns: (is_valid, rejection_reason, latency_ms)
        """
        now = time.time()
        bar_timestamp_sec = open_time_ms / 1000.0
        latency_ms = (now - bar_timestamp_sec) * 1000.0
        
        # 1. Price Bounds Check
        if open_price <= 0 or high_price <= 0 or low_price <= 0 or close_price <= 0:
            self.rejected_candles_count += 1
            reason = f"Non-positive price detected: open={open_price}, high={high_price}, low={low_price}, close={close_price}"
            logger.warning(f"MARKET DATA REJECTED [{symbol}]: {reason}")
            return False, reason, latency_ms
            
        if high_price < low_price or open_price > high_price or close_price > high_price or open_price < low_price or close_price < low_price:
            self.rejected_candles_count += 1
            reason = f"OHLC boundary mismatch: open={open_price}, high={high_price}, low={low_price}, close={close_price}"
            logger.warning(f"MARKET DATA REJECTED [{symbol}]: {reason}")
            return False, reason, latency_ms
            
        # 2. Volume Check
        if volume < 0:
            self.rejected_candles_count += 1
            reason = f"Negative volume detected: {volume}"
            logger.warning(f"MARKET DATA REJECTED [{symbol}]: {reason}")
            return False, reason, latency_ms

        # 3. Duplicate & Ordering Check
        last_ts = self.last_timestamps.get(symbol)
        if last_ts is not None:
            if bar_timestamp_sec == last_ts:
                self.rejected_candles_count += 1
                reason = f"Duplicate candle timestamp: {bar_timestamp_sec}"
                logger.warning(f"MARKET DATA REJECTED [{symbol}]: {reason}")
                return False, reason, latency_ms
            if bar_timestamp_sec < last_ts:
                self.rejected_candles_count += 1
                reason = f"Out-of-order candle timestamp: current={bar_timestamp_sec} < last={last_ts}"
                logger.warning(f"MARKET DATA REJECTED [{symbol}]: {reason}")
                return False, reason, latency_ms

        # 4. Staleness Check
        staleness = now - bar_timestamp_sec
        if staleness > self.max_staleness_sec:
            self.rejected_candles_count += 1
            reason = f"Stale market data: staleness={staleness:.2f}s > max={self.max_staleness_sec}s"
            logger.warning(f"MARKET DATA REJECTED [{symbol}]: {reason}")
            return False, reason, latency_ms

        # Update last timestamp
        self.last_timestamps[symbol] = bar_timestamp_sec
        self.valid_candles_count += 1
        
        latency_record = {
            "symbol": symbol,
            "timeframe": timeframe,
            "market_data_timestamp": bar_timestamp_sec,
            "received_timestamp": now,
            "latency_ms": round(latency_ms, 2)
        }
        self.latency_records.append(latency_record)
        
        return True, None, latency_ms
