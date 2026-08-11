"""
Gemini intelligence layer.

CRITICAL SAFETY PROPERTY: this module can only ever produce a *candidate*
opinion. It cannot place trades. The caller (strategy.py) is responsible for:
  1. Validating the response is well-formed JSON matching GeminiDecision.
  2. Requiring the direction to agree with the independently computed
     technical bias (indicators.py).
  3. Requiring confidence_score > settings.min_confidence_score.
Any failure at any stage collapses to HOLD. There is no code path where raw
model text reaches order placement.
"""
import json
from dataclasses import dataclass
from typing import Any, Literal, Optional

import aiohttp
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.logging_setup import get_logger

logger = get_logger("ai_analyst")

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "decision": {"type": "STRING", "enum": ["BUY", "SELL", "HOLD"]},
        "confidence_score": {"type": "INTEGER"},
        "approved": {"type": "BOOLEAN"},
        "risk_flags": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "reasoning": {"type": "STRING"},
    },
    "required": ["decision", "confidence_score", "approved", "risk_flags", "reasoning"],
}

SYSTEM_INSTRUCTION = """You are the Chief Risk Officer and Lead Quantitative Analyst for Nexus-7 Trading Engine. 
Your SOLE PURPOSE is capital preservation and selective profit extraction.

DEFAULT ASSUMPTION: THE MARKET IS TRAPPING TRADERS. DO NOT APPROVE TRADES UNLESS EXCEPTIONALLY HIGH CONVICTION.

EVALUATION MATRIX:
1. MACRO TREND ALIGNMENT:
   - For LONGs: Price MUST be above the 50-EMA and ADX >= 20.0 (Strong Trend).
   - Reject any counter-trend momentum signals.

2. MOMENTUM & OVEREXTENSION:
   - Reject RSI > 68 for LONGs (Buying the top/exhaustion).
   - Reject RSI < 32 for SHORTs (Selling the bottom).

3. RISK-TO-REWARD & LIQUIDITY:
   - Minimum acceptable R:R ratio is 1:1.67 (Stop Loss: 1.5 ATR / Take Profit: 2.5 ATR).
   - Verify volume ratio >= 0.8. Reject low-volume breakouts.

DECISION PROTOCOL:
- If ANY risk flag is present (e.g. low ADX, overextended RSI, bad R:R, market chop), output "reject" = true or assign a confidence score below 88.
- Assign confidence_score as follows:
  * < 85: Toxic setup / Chop (REJECT)
  * 85 - 87: Mediocre setup / Low volume (REJECT)
  * 88 - 92: Valid setup, strong trend, good volume (APPROVE - Standard Risk 1.0%)
  * 93 - 95: High-conviction setup, volume surge (APPROVE - Medium Risk 1.5%)
  * > 95: A+ Institutional Breakout (APPROVE - High Risk 2.0%)

OUTPUT SCHEMA (STRICT JSON ONLY):
{
  "decision": "BUY" | "SELL" | "HOLD",
  "confidence_score": integer (0 to 100),
  "approved": boolean,
  "risk_flags": [list of detected warnings/reasons],
  "reasoning": "Concise 1-2 sentence justification focusing on market structure and risk."
}
"""


class GeminiDecision(BaseModel):
    decision: Literal["BUY", "SELL", "HOLD"]
    confidence_score: int
    approved: bool
    risk_flags: list[str] = []
    reasoning: str

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("confidence_score out of range")
        return v

    @property
    def action(self) -> str:
        """Compatibility property mapping BUY -> LONG, SELL -> SHORT, HOLD -> HOLD."""
        if self.decision == "BUY":
            return "LONG"
        elif self.decision == "SELL":
            return "SHORT"
        return "HOLD"

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Handle legacy 'action' key if passed instead of 'decision'
            if "decision" not in data and "action" in data:
                act = data.get("action")
                if act == "LONG":
                    data["decision"] = "BUY"
                elif act == "SHORT":
                    data["decision"] = "SELL"
                else:
                    data["decision"] = "HOLD"
            # Auto-populate 'approved' if missing
            if "approved" not in data:
                conf = data.get("confidence_score", 0)
                dec = data.get("decision", "HOLD")
                min_conf = getattr(settings, "min_confidence_score", 88)
                data["approved"] = (conf >= min_conf and dec in ("BUY", "SELL"))
        return data


@dataclass
class AnalystResult:
    decision: Optional[GeminiDecision]
    raw_text: str
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.decision is not None


def _build_prompt(symbol: str, technical: dict, order_book_summary: dict) -> str:
    trade_direction = technical.get("technical_bias", "UNKNOWN")
    current_price = technical.get("close", "N/A")
    rsi_value = technical.get("rsi_14", "N/A")
    macd_val = technical.get("macd", "N/A")
    vol_ratio = technical.get("volume_ratio_vs_avg", "N/A")
    ema_50 = technical.get("ema_50", "N/A")
    ema_200 = technical.get("ema_200", "N/A")
    adx_val = technical.get("adx", "N/A")
    atr_val = technical.get("atr", "N/A")

    payload = {
        "symbol": symbol,
        "signal_direction": trade_direction,
        "current_price": current_price,
        "technical_indicators": technical,
        "order_book_summary": order_book_summary,
    }

    return (
        f"EVALUATE THIS SIGNAL FOR {symbol}:\n"
        f"- Signal Direction: {trade_direction} (BUY/SELL/HOLD or LONG/SHORT/NEUTRAL)\n"
        f"- Current Price: {current_price}\n"
        f"- 50-EMA: {ema_50}\n"
        f"- 200-EMA (Macro Trend): {ema_200}\n"
        f"- ADX: {adx_val}\n"
        f"- Volume Ratio vs Avg: {vol_ratio}\n"
        f"- RSI (14): {rsi_value}\n"
        f"- MACD: {macd_val}\n"
        f"- ATR: {atr_val}\n\n"
        f"Detailed Technical & Order Book Snapshot (JSON):\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Pass this signal through the Institutional Evaluation Matrix and return your JSON assessment."
    )


class RetryableGeminiError(Exception):
    pass


class AIAnalyst:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", getattr(settings, "gemini_api_key", ""))
        self.model = getattr(settings, "gemini_model", "gemini-2.0-flash")
        if not self.api_key or not self.api_key.strip():
            logger.error("CRITICAL: GEMINI_API_KEY missing! Live AI analysis disabled.")

    @retry(
        retry=retry_if_exception_type(RetryableGeminiError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_gemini(self, prompt: str) -> str:
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError("CRITICAL: GEMINI_API_KEY missing! Live AI analysis disabled.")
        url = GEMINI_ENDPOINT.format(model=self.model)
        body = {
            "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": RESPONSE_SCHEMA,
                "temperature": 0.2,
            },
        }
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(
                    url, params={"key": self.api_key}, json=body
                ) as resp:
                    text = await resp.text()
                    if resp.status == 429 or resp.status >= 500:
                        raise RetryableGeminiError(f"Gemini transient error {resp.status}: {text[:200]}")
                    if resp.status != 200:
                        raise RuntimeError(f"Gemini API error {resp.status}: {text[:500]}")
                    return text
            except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError) as e:
                raise RetryableGeminiError(str(e)) from e

    async def analyze(self, symbol: str, technical: dict, order_book_summary: dict) -> AnalystResult:
        if not self.api_key or not self.api_key.strip():
            logger.error("CRITICAL: GEMINI_API_KEY missing! Live AI analysis disabled.")
            return AnalystResult(
                decision=GeminiDecision(
                    decision="HOLD",
                    confidence_score=0,
                    approved=False,
                    risk_flags=["GEMINI_API_KEY missing"],
                    reasoning="CRITICAL: GEMINI_API_KEY missing! Live AI analysis disabled.",
                ),
                raw_text="",
                error="CRITICAL: GEMINI_API_KEY missing! Live AI analysis disabled.",
            )

        prompt = _build_prompt(symbol, technical, order_book_summary)
        try:
            raw_response = await self._call_gemini(prompt)
        except Exception as e:
            logger.error(f"[{symbol}] Gemini call failed after retries: {e}")
            return AnalystResult(decision=None, raw_text="", error=str(e))

        try:
            envelope = json.loads(raw_response)
            # Gemini's generateContent wraps the model output; drill into it.
            candidate_text = envelope["candidates"][0]["content"]["parts"][0]["text"]
            decision_json = json.loads(candidate_text)
            decision = GeminiDecision.model_validate(decision_json)
            return AnalystResult(decision=decision, raw_text=candidate_text)
        except (KeyError, IndexError, json.JSONDecodeError, ValidationError) as e:
            logger.error(f"[{symbol}] Gemini response failed strict validation: {e} | raw={raw_response[:500]}")
            return AnalystResult(decision=None, raw_text=raw_response, error=f"validation_failed: {e}")
