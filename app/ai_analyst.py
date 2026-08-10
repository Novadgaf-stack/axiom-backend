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
from typing import Literal, Optional

import aiohttp
from pydantic import BaseModel, ValidationError, field_validator
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
        "action": {"type": "STRING", "enum": ["LONG", "SHORT", "HOLD"]},
        "confidence_score": {"type": "INTEGER"},
        "risk_flags": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "reasoning": {"type": "STRING"},
    },
    "required": ["action", "confidence_score", "risk_flags", "reasoning"],
}

SYSTEM_INSTRUCTION = """You are an institutional-grade quantitative risk manager. Your primary directive is capital preservation. You do not suffer from FOMO. Your default stance on any technical signal is REJECT unless there is overwhelming, multi-factor confluence. 

You will be provided with a raw technical trading signal, including current price action, volume metrics, and indicator states (e.g., RSI, MACD, EMAs). 

Your task is to validate or invalidate this signal by passing it through the "Antigravity" evaluation matrix.

### PHASE 1: THE ANTIGRAVITY MATRIX (THINKING PROCESS)
Before outputting your final decision, evaluate the following constraints:
1. Trend Alignment (The Gravity Check): Is this signal fighting the macro trend? If the higher timeframe trend is counter to the signal, apply a severe penalty.
2. Volume Validation (The Fuel Check): A breakout without volume is a trap. Is the current candle's volume significantly higher than the rolling average? If volume is flat or declining, reject the trade.
3. Market Structure (The Trap Check): Is price trapped inside a tight range or chop zone? Do not authorize trades in low-volatility consolidation zones unless it is a confirmed breakout with momentum.
4. Mean Reversion Risk: Is the asset overextended? If RSI is overbought (> 75 for LONG) or oversold (< 25 for SHORT) and price is far from key moving averages, reject it as a late entry.

### PHASE 2: SCORING PROTOCOL
Score the setup from 0 to 100 based on the Matrix above.
* 0 - 65: Garbage setup. Ranging market, counter-trend, or low volume. Set action="HOLD".
* 66 - 84: Mediocre setup. Lacks full confluence. Set action="HOLD".
* 85 - 100: "A+" Setup. Perfect alignment of trend, momentum, and volume. Set action="LONG" or "SHORT" matching the valid signal direction.

### PHASE 3: STRICT JSON OUTPUT
Respond ONLY with a valid, parseable JSON object adhering to the schema. Do not include markdown formatting, conversational text, or explanations outside the JSON structure.
"""


class GeminiDecision(BaseModel):
    action: Literal["LONG", "SHORT", "HOLD"]
    confidence_score: int
    risk_flags: list[str] = []
    reasoning: str

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("confidence_score out of range")
        return v


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

    payload = {
        "symbol": symbol,
        "signal_direction": trade_direction,
        "current_price": current_price,
        "technical_indicators": technical,
        "order_book_summary": order_book_summary,
    }

    return (
        f"EVALUATE THIS SIGNAL FOR {symbol}:\n"
        f"- Signal Direction: {trade_direction} (LONG/SHORT/NEUTRAL)\n"
        f"- Current Price: {current_price}\n"
        f"- 50-EMA: {ema_50}\n"
        f"- 200-EMA (Macro Trend): {ema_200}\n"
        f"- Volume Ratio vs Avg: {vol_ratio}\n"
        f"- RSI (14): {rsi_value}\n"
        f"- MACD: {macd_val}\n\n"
        f"Detailed Technical & Order Book Snapshot (JSON):\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Pass this signal through the Antigravity Evaluation Matrix and return your JSON assessment."
    )


class RetryableGeminiError(Exception):
    pass


class AIAnalyst:
    def __init__(self):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY must be set.")
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model

    @retry(
        retry=retry_if_exception_type(RetryableGeminiError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_gemini(self, prompt: str) -> str:
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
