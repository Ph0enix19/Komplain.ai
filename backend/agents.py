from __future__ import annotations

import re
from uuid import uuid4

from backend.models import (
    ContextResult,
    Decision,
    IntakeResult,
    ReasoningResult,
    ResponseResult,
)
from backend.storage import DataManager


def intake_agent(complaint_text: str) -> IntakeResult:
    order_match = re.search(r"\b[A-Z]{2,4}-\d{4,8}\b", complaint_text)
    issue_type = "delivery"

    lowered = complaint_text.lower()
    if any(word in lowered for word in ["broken", "defect", "damage"]):
        issue_type = "damaged_item"
    elif any(word in lowered for word in ["late", "delay", "didn't arrive", "not arrived"]):
        issue_type = "delivery_delay"
    elif any(word in lowered for word in ["wrong item", "incorrect", "different"]):
        issue_type = "wrong_item"

    sentiment = "neutral"
    if any(word in lowered for word in ["angry", "terrible", "worst", "frustrated"]):
        sentiment = "negative"

    return IntakeResult(
        order_id=order_match.group(0) if order_match else None,
        issue_type=issue_type,
        sentiment=sentiment,
    )


def context_agent(data_manager: DataManager, intake: IntakeResult) -> ContextResult:
    if not intake.order_id:
        return ContextResult(
            order_found=False,
            notes="Missing order ID. Ask user to provide an order ID.",
        )

    order = data_manager.get_order(intake.order_id)
    if not order:
        return ContextResult(
            order_found=False,
            notes=f"Order ID {intake.order_id} not found in mock orders.",
        )

    return ContextResult(order_found=True, order_data=order, notes="Order found.")


def reasoning_agent(intake: IntakeResult, context: ContextResult) -> ReasoningResult:
    if not intake.order_id:
        return ReasoningResult(
            decision=Decision.ESCALATE,
            confidence=0.35,
            rationale="Cannot process without order ID.",
            requires_human_review=True,
        )

    if not context.order_found:
        return ReasoningResult(
            decision=Decision.ESCALATE,
            confidence=0.4,
            rationale="Order not found in system.",
            requires_human_review=True,
        )

    status = (context.order_data or {}).get("status", "")
    if intake.issue_type == "damaged_item":
        decision = Decision.REFUND
        confidence = 0.82
        rationale = "Damaged product reported, refund is the quickest resolution."
    elif intake.issue_type in {"delivery_delay", "wrong_item"}:
        decision = Decision.RESHIP
        confidence = 0.76
        rationale = "Reship provides faster fix for delivery/wrong item problems."
    elif status == "DELIVERED":
        decision = Decision.DISMISS
        confidence = 0.7
        rationale = "Order shows delivered and no strong fault signal from complaint."
    else:
        decision = Decision.ESCALATE
        confidence = 0.55
        rationale = "Needs manual review due to unclear issue context."

    return ReasoningResult(
        decision=decision,
        confidence=confidence,
        rationale=rationale,
        requires_human_review=confidence < 0.6,
    )


def response_agent(reasoning: ReasoningResult, context: ContextResult) -> ResponseResult:
    if not context.order_found:
        return ResponseResult(
            english="Thanks for your message. Please share your order ID so we can verify and resolve this quickly.",
            bahasa_malaysia="Terima kasih atas mesej anda. Sila kongsikan ID pesanan anda supaya kami boleh semak dan selesaikan dengan cepat.",
        )

    decision_text = reasoning.decision.value
    en = f"Thanks for your complaint. Our decision is: {decision_text}. {reasoning.rationale}"
    bm = (
        f"Terima kasih atas aduan anda. Keputusan kami ialah: {decision_text}. "
        f"Sebab: {reasoning.rationale}"
    )
    return ResponseResult(english=en, bahasa_malaysia=bm)


def supervisor_logic(reasoning: ReasoningResult) -> dict:
    return {
        "requires_human_review": reasoning.requires_human_review,
        "priority": "high" if reasoning.requires_human_review else "normal",
        "supervisor_note": (
            "Escalate to human support."
            if reasoning.requires_human_review
            else "Auto-resolution is acceptable."
        ),
    }


def build_event(complaint_id: str, step: str, message: str, payload: dict | None = None) -> dict:
    from datetime import datetime, timezone

    return {
        "id": str(uuid4()),
        "complaint_id": complaint_id,
        "step": step,
        "message": message,
        "payload": payload or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
