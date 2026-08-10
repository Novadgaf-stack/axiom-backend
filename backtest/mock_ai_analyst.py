"""
Drop-in replacements for app.ai_analyst.AIAnalyst, sharing its exact return
type (AnalystResult wrapping a GeminiDecision) so app.strategy.StrategyEngine
can be reused UNMODIFIED in the backtest — the dual-confirmation gating logic
under test is then guaranteed identical to what live trading runs, instead of
a reimplementation that could quietly drift out of sync.

Modes:
  technical_only  — confidence always 100, action always mirrors the
                     technical bias. This effectively disables the AI gate
                     (it never disagrees, never blocks on confidence), which
                     is exactly what "technical-only" means for a comparative
                     backtest.
  ai_mirror       — a deterministic heuristic that scales confidence with how
                     strong the indicator readings are (RSI distance from
                     center, MACD histogram size, volume). This is NOT a
                     claim that Gemini would say the same thing — it's a
                     cheap, reproducible stand-in so the AI-gate's FILTERING
                     BEHAVIOR (rejecting weak setups) can be backtested
                     without thousands of live API calls. Treat results from
                     this mode as "what if the AI layer filtered strength
                     correctly" — an upper-bound sanity check, not a Gemini
                     forecast.
  ai_random       — confidence and action are random noise. This is a null
                     control: if ai_mirror doesn't outperform ai_random by a
                     meaningful margin, that's evidence the confidence
                     heuristic (and by extension, an under-informative real
                     AI layer) isn't adding real filtering value.
  ai_live         — wraps the REAL app.ai_analyst.AIAnalyst and makes actual
                     Gemini calls. Slow, costs money, and rate-limited by
                     Gemini's API — only use on a short date range or a
                     capped number of calls.
"""
import random
from app.ai_analyst import AnalystResult, GeminiDecision


class MockAiAnalyst:
    def __init__(self, mode: str = "ai_mirror", seed: int = 42):
        assert mode in ("technical_only", "ai_mirror", "ai_random"), f"unknown mock mode {mode}"
        self.mode = mode
        self._rng = random.Random(seed)
        self.call_count = 0

    async def analyze(self, symbol: str, technical: dict, order_book_summary: dict) -> AnalystResult:
        self.call_count += 1
        bias = technical.get("technical_bias", "NEUTRAL")

        if self.mode == "technical_only":
            action = bias if bias in ("LONG", "SHORT") else "HOLD"
            confidence = 100
            reasoning = "technical_only mode: AI gate disabled, mirrors technical bias at max confidence."

        elif self.mode == "ai_mirror":
            action = bias if bias in ("LONG", "SHORT") else "HOLD"
            rsi = technical.get("rsi_14", 50.0)
            macd = technical.get("macd", 0.0)
            close = technical.get("close", 1.0) or 1.0
            vol_ratio = technical.get("volume_ratio_vs_avg", 1.0)

            rsi_strength = min(abs(rsi - 50.0) / 25.0, 1.0)          # 0..1
            macd_strength = min(abs(macd) / (abs(close) * 0.002 + 1e-9), 1.0)  # 0..1
            vol_strength = min(max(vol_ratio, 0.0) / 2.0, 1.0)       # 0..1
            composite = 0.5 * rsi_strength + 0.3 * macd_strength + 0.2 * vol_strength
            confidence = int(max(0, min(100, round(50 + 50 * composite))))
            reasoning = f"ai_mirror heuristic: rsi_strength={rsi_strength:.2f} macd_strength={macd_strength:.2f} vol_strength={vol_strength:.2f}"

        else:  # ai_random
            action = self._rng.choice(["LONG", "SHORT", "HOLD"])
            confidence = self._rng.randint(0, 100)
            reasoning = "ai_random null-control mode: noise, no relationship to the data."

        decision = GeminiDecision(action=action, confidence_score=confidence, reasoning=reasoning)
        return AnalystResult(decision=decision, raw_text="{}")


def synthetic_order_book_summary(candle: list) -> dict:
    """
    Historical L2 order book snapshots aren't available from OHLCV data.
    This builds a plausible-shaped stand-in from the candle itself so the
    AI prompt format matches production, purely for ai_live mode (the mock
    modes above don't even look at it). NOT a substitute for a real book —
    the imbalance figure especially is a rough proxy, not a measurement.
    """
    _, o, h, l, c, v = candle
    mid = (h + l) / 2
    spread = max((h - l) * 0.05, mid * 0.0001)
    bullish = c >= o
    imbalance = 0.15 if bullish else -0.15
    return {
        "best_bid": round(mid - spread / 2, 6),
        "best_ask": round(mid + spread / 2, 6),
        "spread": round(spread, 6),
        "top10_bid_volume": round(v * (0.55 if bullish else 0.45), 4),
        "top10_ask_volume": round(v * (0.45 if bullish else 0.55), 4),
        "order_book_imbalance": imbalance,
        "note": "synthetic proxy derived from OHLCV — no real historical order book data",
    }
