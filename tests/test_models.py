from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.models import ComplaintCreate, Decision, ReasoningResult


def test_complaint_create_rejects_empty_text() -> None:
    with pytest.raises(ValidationError):
        ComplaintCreate(complaint_text="")


def test_complaint_create_accepts_valid_text_and_optional_order_id() -> None:
    payload = ComplaintCreate(complaint_text="Item arrived damaged", order_id="KM-1001")

    assert payload.complaint_text == "Item arrived damaged"
    assert payload.order_id == "KM-1001"


def test_decision_enum_values() -> None:
    assert {decision.value for decision in Decision} == {
        "REFUND",
        "RESHIP",
        "ESCALATE",
        "DISMISS",
    }


def test_reasoning_result_clamps_confidence_to_supported_range() -> None:
    too_high = ReasoningResult(decision=Decision.REFUND, confidence=1.5, rationale="Clear merchant fault")
    too_low = ReasoningResult(decision=Decision.DISMISS, confidence=-0.25, rationale="No order match")

    assert too_high.confidence == 1
    assert too_low.confidence == 0
