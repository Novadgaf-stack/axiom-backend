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
        "reasoning": {"type": "STRING"},
    },
    "required": ["action", "confidence_score", "reasoning"],
}

SYSTEM_INSTRUCTION = (
    "You are a disciplined, risk-averse crypto market analyst. You are given a "
    "structured snapshot of technical indicators and order book state for one "
    "trading pair. Respond ONLY with the requested JSON object — no markdown, "
    "no prose outside the JSON. Be conservative: prefer HOLD unless the signal "
    "is genuinely strong. confidence_score must be an integer from 0 to 100 "
    "reflecting your genuine conviction, not a rounded default like 50 or 90."
)


class GeminiDecision(BaseModel):
    action: Literal["LONG", "SHORT", "HOLD"]
    confidence_score: int
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
    payload = {
        "symbol": symbol,
        "technical_indicators": technical,
        "order_book_summary": order_book_summary,
    }
    return (
        "Market snapshot (JSON):\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Given this data, decide: LONG, SHORT, or HOLD. "
        "Return the JSON object described in your instructions."
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
