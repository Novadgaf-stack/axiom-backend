"""
The decision pipeline. This is the ONLY place a trade signal is produced,
and it enforces the dual-confirmation rule end to end:

    technical_bias (quantitative, from indicators.py)
        AND
    Gemini action + confidence_score > MIN_CONFIDENCE_SCORE (ai_analyst.py)
        must AGREE on direction
        =>
    only then does risk.py get a chance to size and approve the trade.

Any disagreement, low confidence, invalid AI response, or neutral technical
bias results in HOLD with the reason recorded for the audit trail.
"""
from dataclasses import dataclass
from typing import Optional

from app.ai_analyst import AIAnalyst, AnalystResult
from app.indicators import TechnicalSnapshot, compute_snapshot
from app.config import settings
from app.logging_setup import get_logger

logger = get_logger("strategy")


@dataclass
class Decision:
    symbol: str
    action: str  # "LONG" | "SHORT" | "HOLD"
    technical: Optional[TechnicalSnapshot]
    analyst: Optional[AnalystResult]
    reject_reason: Optional[str] = None

    @property
    def is_actionable(self) -> bool:
        return self.action in ("LONG", "SHORT") and self.reject_reason is None


def _summarize_order_book(order_book: dict) -> dict:
    bids = order_book.get("bids", [])[:10]
    asks = order_book.get("asks", [])[:10]
    bid_volume = sum(b[1] for b in bids)
    ask_volume = sum(a[1] for a in asks)
    best_bid = bids[0][0] if bids else None
    best_ask = asks[0][0] if asks else None
    spread = (best_ask - best_bid) if (best_bid and best_ask) else None
    imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
    return {
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "top10_bid_volume": round(bid_volume, 4),
        "top10_ask_volume": round(ask_volume, 4),
        "order_book_imbalance": round(imbalance, 4),  # +1 = all bids, -1 = all asks
    }


class StrategyEngine:
    def __init__(self, analyst: AIAnalyst):
        self.analyst = analyst

    async def evaluate(self, symbol: str, ohlcv: list, order_book: dict) -> Decision:
        min_adx = getattr(settings, "min_adx", 20.0)
        min_vol = getattr(settings, "min_volume_ratio", 0.7)
        technical = compute_snapshot(
            ohlcv, atr_period=settings.atr_period, min_volume_ratio=min_vol, min_adx=min_adx
        )
        if technical is None:
            return Decision(symbol, "HOLD", None, None, reject_reason="insufficient_candle_history")

        if settings.require_technical_confirmation and technical.bias == "NEUTRAL":
            reason = "adx_below_threshold" if technical.adx < min_adx else "technical_bias_neutral"
            return Decision(symbol, "HOLD", technical, None, reject_reason=reason)

        if getattr(settings, "enable_session_filter", False):
            # Check UTC timestamp of last closed candle
            last_closed_ts = ohlcv[-2][0] if len(ohlcv) >= 2 else 0
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(last_closed_ts / 1000, tz=timezone.utc)
            start_h = getattr(settings, "session_start_hour", 12)
            end_h = getattr(settings, "session_end_hour", 20)
            if not (start_h <= dt.hour < end_h):
                return Decision(symbol, "HOLD", technical, None, reject_reason="outside_session_window")

        ob_summary = _summarize_order_book(order_book)
        analyst_result = await self.analyst.analyze(symbol, technical.to_prompt_dict(), ob_summary)

        if not analyst_result.is_valid:
            return Decision(symbol, "HOLD", technical, analyst_result, reject_reason="ai_response_invalid")

        decision = analyst_result.decision

        if decision.action == "HOLD":
            return Decision(symbol, "HOLD", technical, analyst_result, reject_reason="ai_said_hold")

        if decision.confidence_score <= settings.min_confidence_score:
            return Decision(
                symbol, "HOLD", technical, analyst_result,
                reject_reason=f"confidence_{decision.confidence_score}_below_threshold_{settings.min_confidence_score}",
            )

        if settings.require_technical_confirmation and decision.action != technical.bias:
            return Decision(
                symbol, "HOLD", technical, analyst_result,
                reject_reason=f"ai_{decision.action}_disagrees_with_technical_{technical.bias}",
            )

        # Both signals agree and pass threshold — this is an actionable call.
        return Decision(symbol, decision.action, technical, analyst_result, reject_reason=None)
