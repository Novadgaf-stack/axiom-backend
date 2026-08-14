"""
Unit tests for app.ai_analyst and Institutional Risk Manager logic.
"""
import json
import pytest
from pydantic import ValidationError

from app.ai_analyst import AIAnalyst, GeminiDecision, AnalystResult, SYSTEM_INSTRUCTION, RESPONSE_SCHEMA
from app.config import settings


def test_system_instruction_contains_institutional_matrix():
    assert "Chief Risk Officer" in SYSTEM_INSTRUCTION
    assert "DEFAULT ASSUMPTION: THE MARKET IS TRAPPING TRADERS" in SYSTEM_INSTRUCTION
    assert "EVALUATION MATRIX:" in SYSTEM_INSTRUCTION
    assert "ADX >= 20.0" in SYSTEM_INSTRUCTION
    assert "RSI > 68" in SYSTEM_INSTRUCTION
    assert "confidence_score below 88" in SYSTEM_INSTRUCTION or "below 88" in SYSTEM_INSTRUCTION


def test_response_schema_structure():
    assert RESPONSE_SCHEMA["type"] == "OBJECT"
    props = RESPONSE_SCHEMA["properties"]
    assert "decision" in props
    assert props["decision"]["enum"] == ["BUY", "SELL", "HOLD"]
    assert "confidence_score" in props
    assert "approved" in props
    assert "risk_flags" in props
    assert "reasoning" in props


def test_gemini_decision_parsing_buy():
    payload = {
        "decision": "BUY",
        "confidence_score": 92,
        "approved": True,
        "risk_flags": [],
        "reasoning": "Strong trend alignment above 50-EMA with high volume."
    }
    dec = GeminiDecision.model_validate(payload)
    assert dec.decision == "BUY"
    assert dec.confidence_score == 92
    assert dec.approved is True
    assert dec.action == "LONG"


def test_gemini_decision_parsing_sell():
    payload = {
        "decision": "SELL",
        "confidence_score": 95,
        "approved": True,
        "risk_flags": [],
        "reasoning": "Breakout below support with massive sell volume."
    }
    dec = GeminiDecision.model_validate(payload)
    assert dec.decision == "SELL"
    assert dec.confidence_score == 95
    assert dec.approved is True
    assert dec.action == "SHORT"


def test_gemini_decision_parsing_hold():
    payload = {
        "decision": "HOLD",
        "confidence_score": 65,
        "approved": False,
        "risk_flags": ["Low ADX", "Overextended RSI"],
        "reasoning": "Ranging market with dead volume."
    }
    dec = GeminiDecision.model_validate(payload)
    assert dec.decision == "HOLD"
    assert dec.confidence_score == 65
    assert dec.approved is False
    assert dec.action == "HOLD"


def test_gemini_decision_clamp_confidence_validation():
    with pytest.raises(ValidationError):
        GeminiDecision.model_validate({
            "decision": "BUY",
            "confidence_score": 105,
            "approved": True,
            "risk_flags": [],
            "reasoning": "Invalid confidence"
        })

    with pytest.raises(ValidationError):
        GeminiDecision.model_validate({
            "decision": "BUY",
            "confidence_score": -5,
            "approved": True,
            "risk_flags": [],
            "reasoning": "Negative confidence"
        })


def test_legacy_action_input_compatibility():
    payload = {
        "action": "LONG",
        "confidence_score": 90,
        "risk_flags": [],
        "reasoning": "Legacy schema payload"
    }
    dec = GeminiDecision.model_validate(payload)
    assert dec.decision == "BUY"
    assert dec.action == "LONG"
    assert dec.approved is True


@pytest.mark.asyncio
async def test_missing_gemini_api_key_disables_analysis(monkeypatch, caplog):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    object.__setattr__(settings, "gemini_api_key", "")
    analyst = AIAnalyst()

    result = await analyst.analyze("BTC/USDT", {}, {})
    assert not result.is_valid or result.decision.approved is False
    assert result.decision.decision == "HOLD"
    assert result.decision.confidence_score == 0


@pytest.mark.asyncio
async def test_valid_gemini_response_parsing(monkeypatch):
    object.__setattr__(settings, "gemini_api_key", "mock_key_for_testing")
    analyst = AIAnalyst()

    mock_envelope = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "decision": "BUY",
                                "confidence_score": 93,
                                "approved": True,
                                "risk_flags": [],
                                "reasoning": "High-conviction trend setup."
                            })
                        }
                    ]
                }
            }
        ]
    }

    async def mock_call_gemini(prompt: str) -> str:
        return json.dumps(mock_envelope)

    monkeypatch.setattr(analyst, "_call_gemini", mock_call_gemini)

    result = await analyst.analyze("BTC/USDT", {"technical_bias": "LONG"}, {})
    assert result.is_valid
    assert result.decision.decision == "BUY"
    assert result.decision.action == "LONG"
    assert result.decision.confidence_score == 93
    assert result.decision.approved is True


def test_config_min_confidence_default():
    assert settings.min_confidence_score == 82
    assert getattr(settings, "AI_MIN_CONFIDENCE") == 82
