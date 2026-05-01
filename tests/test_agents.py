from __future__ import annotations

import pytest

from backend.agents import (
    context_agent,
    fallback_intake,
    intake_agent,
    reasoning_agent,
    response_agent,
    supervisor_logic,
)
from backend.models import ContextResult, Decision, IntakeResult, ReasoningResult
from backend.storage import DataManager


class FakeLLM:
    def __init__(self, payloads: list[dict] | None = None) -> None:
        self.payloads = payloads or []
        self.prompts: list[str] = []

    async def chat_json(self, prompt: str, *_args, **_kwargs) -> dict:
        self.prompts.append(prompt)
        if not self.payloads:
            raise RuntimeError("No fake payload configured")
        return self.payloads.pop(0)


class FakeUsageLLM(FakeLLM):
    async def chat_json_with_usage(self, prompt: str, *args, **kwargs) -> tuple[dict, dict]:
        payload = await self.chat_json(prompt, *args, **kwargs)
        return payload, {
            "input_tokens": 12,
            "output_tokens": 5,
            "provider_used": "groq",
            "fallback_used": True,
            "fallback_reason": "rate_limit",
        }


@pytest.mark.asyncio
async def test_intake_extracts_order_id_from_llm_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "customer_name": "Aisyah",
                "order_id": " km-1001 ",
                "issue_type": "damaged",
                "sentiment": "negative",
                "language": "english",
            }
        ]
    )

    result = await intake_agent(llm, "Order KM-1001 arrived damaged")

    assert result.order_id == "KM-1001"
    assert result.issue_type == "damaged_item"
    assert result.language == "EN"


@pytest.mark.asyncio
async def test_agent_metrics_include_provider_fallback_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeUsageLLM(
        [
            {
                "customer_name": "Aisyah",
                "order_id": "KM-1001",
                "issue_type": "damaged_item",
                "sentiment": "negative",
                "language": "EN",
            }
        ]
    )
    metrics = {"agent": "intake", "input_tokens": 0, "output_tokens": 0, "execution_mode": "unknown"}

    result = await intake_agent(llm, "Order KM-1001 arrived damaged", metrics=metrics)

    assert result.order_id == "KM-1001"
    assert metrics["input_tokens"] == 12
    assert metrics["output_tokens"] == 5
    assert metrics["provider_used"] == "groq"
    assert metrics["fallback_used"] is True
    assert metrics["fallback_reason"] == "rate_limit"
    assert metrics["execution_mode"] == "fallback"


def test_fallback_intake_extracts_order_id_without_llm() -> None:
    result = fallback_intake("Barang rosak for order ord-1887")

    assert result["order_id"] == "ORD-1887"
    assert result["issue_type"] == "damaged_item"
    assert result["language"] == "Manglish"


@pytest.mark.asyncio
async def test_intake_recovers_order_id_when_llm_omits_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "customer_name": None,
                "order_id": None,
                "issue_type": "wrong_item",
                "sentiment": "neutral",
                "language": "EN",
            }
        ]
    )

    result = await intake_agent(llm, "I ordered KM-1003 but received the wrong item.")

    assert result.order_id == "KM-1003"
    assert result.issue_type == "wrong_item"


def test_fallback_intake_detects_mixed_language() -> None:
    result = fallback_intake("Saya nak refund. Barang rosak.")

    assert result["language"] == "Manglish"


@pytest.mark.asyncio
async def test_context_agent_attaches_order_data(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "false")
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()
    manager.orders = [{"order_id": "KM-1001", "customer_name": "Aisyah", "status": "DELIVERED"}]

    result = await context_agent(FakeLLM(), manager, IntakeResult(order_id="KM-1001", issue_type="damaged_item"))

    assert result.order_found is True
    assert result.order_data["customer_name"] == "Aisyah"


@pytest.mark.asyncio
async def test_reasoning_returns_valid_enum_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "decision": "replacement",
                "confidence": 0.7,
                "rationale": "Wrong item can be replaced.",
                "requires_human_review": False,
            }
        ]
    )
    intake = IntakeResult(order_id="KM-1002", issue_type="wrong_item", sentiment="negative")
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1002"}, notes="Order found")

    result = await reasoning_agent(llm, "I received the wrong item", intake, context)

    assert result.decision == Decision.RESHIP
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_reasoning_prefers_reship_for_wrong_item_with_order_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "decision": "ESCALATE",
                "confidence": 0.7,
                "rationale": "Manual review requested.",
                "requires_human_review": True,
            }
        ]
    )
    intake = IntakeResult(order_id="KM-1003", issue_type="wrong_item", sentiment="neutral")
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1003"}, notes="Order found")

    result = await reasoning_agent(llm, "I received the wrong item for KM-1003.", intake, context)

    assert result.decision == Decision.RESHIP
    assert result.requires_human_review is False
    assert result.confidence >= 0.82


@pytest.mark.asyncio
async def test_reasoning_falls_back_for_invalid_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "decision": "UNKNOWN_ACTION",
                "confidence": 0.9,
                "rationale": "Invalid decision.",
                "requires_human_review": False,
            }
        ]
    )
    intake = IntakeResult(order_id=None, issue_type="unknown", sentiment="negative")
    context = ContextResult(order_found=False, notes="No order")

    result = await reasoning_agent(llm, "No order details", intake, context)

    assert result.decision == Decision.ESCALATE
    assert result.requires_human_review is True


@pytest.mark.asyncio
async def test_response_agent_outputs_english_and_bahasa_malaysia(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "english": "We approved a refund.",
                "bahasa_malaysia": "Kami telah meluluskan bayaran balik.",
            }
        ]
    )
    reasoning = ReasoningResult(decision=Decision.REFUND, confidence=0.95, rationale="Damaged item")
    context = ContextResult(order_found=True, order_data={"customer_name": "Aisyah"}, notes="Order found")

    result = await response_agent(llm, "Damaged item", reasoning, context)

    assert result.english == "We approved a refund."
    assert result.bahasa_malaysia == "Kami telah meluluskan bayaran balik."


@pytest.mark.asyncio
async def test_supervisor_clears_review_for_high_confidence_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "requires_human_review": True,
                "priority": "high",
                "supervisor_note": "Manual review requested.",
            }
        ]
    )
    reasoning = ReasoningResult(
        decision=Decision.RESHIP,
        confidence=0.92,
        rationale="Wrong item can be replaced.",
        requires_human_review=False,
    )
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1003"}, notes="Order found")

    result = await supervisor_logic(llm, reasoning, context)

    assert result["requires_human_review"] is False
    assert result["priority"] == "normal"


@pytest.mark.asyncio
async def test_supervisor_logic_returns_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "false")
    reasoning = ReasoningResult(
        decision=Decision.ESCALATE,
        confidence=0.7,
        rationale="Needs manual review",
        requires_human_review=True,
    )
    context = ContextResult(order_found=False, notes="Missing order")

    result = await supervisor_logic(FakeLLM(), reasoning, context)

    assert result["requires_human_review"] is True
    assert result["priority"] == "high"
    assert result["supervisor_note"]
