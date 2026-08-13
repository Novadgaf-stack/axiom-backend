"""
NEXUS-7 — ORDER BOOK FEATURE TRANSFORMER (RESEARCH V11)
Transforms raw CCXT public trades and L2 order book depth into active mathematical strategy features.
"""
from typing import Dict, List
import numpy as np


class OrderBookFeatureTransformer:
    """Transforms raw tick trades and L2 depth into 4 active mathematical strategy features."""

    @staticmethod
    def compute_l2_imbalance(bid_vol: float, ask_vol: float) -> float:
        total_vol = bid_vol + ask_vol
        if total_vol <= 0:
            return 0.0
        return (bid_vol - ask_vol) / total_vol

    @staticmethod
    def compute_tick_cvd_surge(trades: List[Dict]) -> float:
        if not trades:
            return 0.0
        buy_vol = sum(t["amount"] for t in trades if t["side"] == "buy")
        sell_vol = sum(t["amount"] for t in trades if t["side"] == "sell")
        total_vol = buy_vol + sell_vol
        if total_vol <= 0:
            return 0.0
        return (buy_vol - sell_vol) / total_vol

    @staticmethod
    def compute_spread_pressure(bids: List[List[float]], asks: List[List[float]]) -> float:
        if not bids or not asks:
            return 1.0
        top3_bid = sum(b[1] for b in bids[:3])
        top3_ask = sum(a[1] for a in asks[:3])
        if top3_bid <= 0:
            return 1.0
        return top3_ask / top3_bid

    @staticmethod
    def generate_order_book_features(trades: List[Dict], depth: Dict) -> Dict[str, float]:
        bid_vol = depth.get("bid_vol", 0.0)
        ask_vol = depth.get("ask_vol", 0.0)
        bids = depth.get("bids", [])
        asks = depth.get("asks", [])

        l2_imbalance = OrderBookFeatureTransformer.compute_l2_imbalance(bid_vol, ask_vol)
        tick_cvd_surge = OrderBookFeatureTransformer.compute_tick_cvd_surge(trades)
        spread_pressure = OrderBookFeatureTransformer.compute_spread_pressure(bids, asks)

        # Microstructure signal trigger: True Order Flow Buy Signal if imbalance > 0.15 and CVD > 0.10
        signal_bias = 0
        if l2_imbalance > 0.15 and tick_cvd_surge > 0.10:
            signal_bias = 1
        elif l2_imbalance < -0.15 and tick_cvd_surge < -0.10:
            signal_bias = -1

        return {
            "l2_imbalance": round(l2_imbalance, 4),
            "tick_cvd_surge": round(tick_cvd_surge, 4),
            "spread_pressure": round(spread_pressure, 4),
            "signal_bias": signal_bias,
            "classification": "TICK_LEVEL_TRUE_ORDER_FLOW",
        }
