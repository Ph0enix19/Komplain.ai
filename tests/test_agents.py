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
from backend.models import (
    ContextResult,
    Decision,
    ImageAnalysisResult,
    IntakeResult,
    ReasoningResult,
)
from backend.storage import DataManager


class FakeLLM:
    def __init__(self, payloads: list[dict] | None = None) -> None:
        self.payloads = payloads or []
        self.prompts: list[str] = []
        self.systems: list[str] = []

    async def chat_json(self, prompt: str, *_args, **kwargs) -> dict:
        self.prompts.append(prompt)
        if "system" in kwargs:
            self.systems.append(kwargs["system"])
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
    assert "English only" in llm.systems[0]


@pytest.mark.asyncio
async def test_reasoning_processes_manglish_but_outputs_english_internal_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "decision": "REFUND",
                "confidence": 0.92,
                "rationale": "Barang pelanggan rosak dan perlu bayaran balik.",
                "requires_human_review": False,
            }
        ]
    )
    intake = IntakeResult(order_id="KM-1001", issue_type="damaged_item", sentiment="negative", language="Manglish")
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1001"}, notes="Order found")

    result = await reasoning_agent(llm, "Saya punya barang rosak for order KM-1001", intake, context)

    assert result.decision == Decision.REFUND
    assert result.rationale == "The customer reports a damaged item for an order that exists in the system."
    assert "barang" not in result.rationale.lower()


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
async def test_reasoning_prompt_receives_image_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "decision": "REFUND",
                "confidence": 0.81,
                "rationale": "Complaint and image show damage.",
                "requires_human_review": False,
            }
        ]
    )
    intake = IntakeResult(order_id="KM-1001", issue_type="damaged_item", sentiment="negative")
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1001"}, notes="Order found")
    image_analysis = ImageAnalysisResult(
        image_provided=True,
        image_analyzed=True,
        damage_detected=True,
        damage_level="major",
        matches_order_item=True,
        confidence=0.91,
        evidence="Torn packaging is visible.",
    )

    result = await reasoning_agent(llm, "Box arrived damaged", intake, context, image_analysis)

    assert "Visual evidence" in llm.prompts[0]
    assert "Torn packaging is visible" in llm.prompts[0]
    assert result.decision == Decision.REFUND
    assert result.confidence >= 0.91


@pytest.mark.asyncio
async def test_reasoning_clarifies_when_image_conflicts_with_damage_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "decision": "REFUND",
                "confidence": 0.92,
                "rationale": "Text says damaged.",
                "requires_human_review": False,
            }
        ]
    )
    intake = IntakeResult(order_id="KM-1001", issue_type="damaged_item", sentiment="negative")
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1001"}, notes="Order found")
    image_analysis = ImageAnalysisResult(
        image_provided=True,
        image_analyzed=True,
        damage_detected=False,
        damage_level="none",
        matches_order_item=True,
        confidence=0.95,
        evidence="No visible damage.",
    )

    result = await reasoning_agent(llm, "Box arrived damaged", intake, context, image_analysis)

    assert result.decision == Decision.CLARIFY
    assert result.requires_human_review is True
    assert result.confidence <= 0.74


@pytest.mark.asyncio
async def test_reasoning_requests_clarification_for_missing_claim_with_package_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "decision": "REFUND",
                "confidence": 0.91,
                "rationale": "Refund requested.",
                "requires_human_review": False,
            }
        ]
    )
    intake = IntakeResult(order_id="KM-1001", issue_type="delivery_delay", sentiment="negative")
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1001"}, notes="Order found")
    image_analysis = ImageAnalysisResult(
        image_provided=True,
        image_analyzed=True,
        package_visible=True,
        damage_detected=True,
        damage_level="major",
        matches_order_item=True,
        confidence=0.94,
        evidence="A torn package is visible.",
    )

    result = await reasoning_agent(
        llm,
        "My order is missing where is it. I want a refund.",
        intake,
        context,
        image_analysis,
    )

    assert result.decision == Decision.CLARIFY
    assert result.requires_human_review is True
    assert result.clarification_needed is True
    assert (
        result.clarification_message
        == "Please confirm whether you received the package or whether the order is still missing."
    )
    assert "Contradiction detected" in result.rationale


@pytest.mark.asyncio
async def test_response_agent_asks_for_clarification_without_refund_or_reship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    reasoning = ReasoningResult(
        decision=Decision.CLARIFY,
        confidence=0.82,
        rationale="Contradiction detected.",
        requires_human_review=True,
        clarification_needed=True,
        clarification_message="Please confirm if you received the package or if it is still missing.",
    )
    context = ContextResult(order_found=True, order_data={"customer_name": "Aisyah", "item": "Bluetooth Speaker"})

    result = await response_agent(FakeLLM(), "My order is missing", reasoning, context)

    assert "confirm" in result.english.lower()
    assert "refund" not in result.english.lower()
    assert "reship" not in result.english.lower()
    assert "sahkan" in result.bahasa_malaysia.lower()


@pytest.mark.asyncio
async def test_clarification_response_does_not_duplicate_customer_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    reasoning = ReasoningResult(
        decision=Decision.CLARIFY,
        confidence=0.74,
        rationale="Complaint reports damage but visual evidence does not show clear damage.",
        requires_human_review=True,
        clarification_needed=True,
        clarification_message="Thank you for reaching out, Hannah. Could you please confirm the issue?",
    )
    context = ContextResult(order_found=True, order_data={"customer_name": "Hannah", "item": "Linen Midi Dress"})

    result = await response_agent(FakeLLM(), "The dress is damaged", reasoning, context)

    assert result.english.count("Hannah") == 1
    assert "Thank you for reaching out, Hannah" not in result.english
    assert "refund" not in result.english.lower()


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
async def test_response_agent_replaces_demo_customer_with_order_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "english": "Dear Demo Customer, we arranged a reshipment.",
                "bahasa_malaysia": "Kehadapan Demo Customer, kami telah mengatur penghantaran semula.",
            }
        ]
    )
    reasoning = ReasoningResult(decision=Decision.RESHIP, confidence=0.9, rationale="Wrong size")
    context = ContextResult(
        order_found=True,
        order_data={"customer_name": "Nadia Rahman", "item": "Classic Cotton T-Shirt - White M"},
        notes="Order found",
    )

    result = await response_agent(llm, "Wrong size", reasoning, context)

    assert "Demo Customer" not in result.english
    assert "Demo Customer" not in result.bahasa_malaysia
    assert "Nadia Rahman" in result.english
    assert "Nadia Rahman" in result.bahasa_malaysia


@pytest.mark.asyncio
async def test_fallback_response_uses_neutral_greeting_for_placeholder_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "false")
    reasoning = ReasoningResult(decision=Decision.RESHIP, confidence=0.9, rationale="Wrong size")
    context = ContextResult(
        order_found=True,
        order_data={"customer_name": "Demo Customer", "item": "Classic Cotton T-Shirt - White M"},
        notes="Order found",
    )

    result = await response_agent(FakeLLM(), "Wrong size", reasoning, context)

    assert "Demo Customer" not in result.english
    assert result.english.startswith("Hi there,")


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


@pytest.mark.asyncio
async def test_supervisor_processes_bm_context_but_outputs_english_note(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    llm = FakeLLM(
        [
            {
                "requires_human_review": True,
                "priority": "high",
                "supervisor_note": "Kes pelanggan memerlukan semakan manusia.",
            }
        ]
    )
    reasoning = ReasoningResult(
        decision=Decision.ESCALATE,
        confidence=0.7,
        rationale="Needs review",
        requires_human_review=True,
    )
    context = ContextResult(order_found=True, order_data={"order_id": "KM-1001"}, notes="Pesanan dijumpai")

    result = await supervisor_logic(llm, reasoning, context)

    assert result["priority"] == "high"
    assert (
        result["supervisor_note"]
        == "Seller action: review the case manually because the order context or evidence is incomplete."
    )
    assert "pelanggan" not in result["supervisor_note"].lower()
    assert "English only" in llm.systems[0]
