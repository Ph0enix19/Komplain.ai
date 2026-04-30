from __future__ import annotations

import asyncio
import os
import re
from uuid import uuid4

from pydantic import ValidationError

from backend.llm import ILMUClient
from backend.models import (
    ContextResult,
    IntakeResult,
    ReasoningResult,
    ResponseResult,
)
from backend.storage import DataManager


INTAKE_SYSTEM = """You are the intake agent for a customer complaints workflow.
Read the complaint and extract structured fields.
Return only valid JSON with exactly these keys:
- customer_name: string or null
- order_id: string or null
- issue_type: one of "damaged_item", "delivery_delay", "wrong_item", "delivery", "billing", "refund_request", "unknown"
- sentiment: one of "positive", "neutral", "negative"
Do not include explanations or markdown."""

CONTEXT_SYSTEM = """You are the context agent for a customer complaints workflow.
You receive the structured intake result and any order lookup result from the internal system.
Return only valid JSON with exactly these keys:
- order_found: boolean
- notes: short string
Base order_found on the provided order lookup result. Do not invent order data."""

REASONING_SYSTEM = """You are the reasoning agent for a customer complaints workflow.
Decide the next action using the provided complaint, intake, and order context.
Return only valid JSON with exactly these keys:
- decision: one of "REFUND", "RESHIP", "ESCALATE", "DISMISS"
- confidence: number between 0 and 1
- rationale: short string
- requires_human_review: boolean
Prefer REFUND for clearly damaged delivered items.
Prefer RESHIP for wrong item or delivery delay when a replacement is appropriate.
Use ESCALATE when the order is missing, unclear, risky, or needs manual review."""

RESPONSE_SYSTEM = """You are the response agent for a customer complaints workflow.
Draft customer-facing replies based on the complaint, decision, and order context.
Return only valid JSON with exactly these keys:
- english: string
- bahasa_malaysia: string
Keep the message concise, empathetic, and aligned with the decision."""

SUPERVISOR_SYSTEM = """You are the supervisor agent for a customer complaints workflow.
Review the reasoning result and decide whether the case needs human escalation.
Return only valid JSON with exactly these keys:
- requires_human_review: boolean
- priority: one of "normal", "high"
- supervisor_note: short string"""

AGENT_LLM_TIMEOUT_SECONDS = float(os.getenv("AGENT_LLM_TIMEOUT_SECONDS", "180"))


def use_llm_agents() -> bool:
    return os.getenv("USE_LLM_AGENTS", "true").lower() in {"1", "true", "yes", "on"}


def _validated(model_cls, payload: dict, error_message: str):
    try:
        return model_cls(**payload)
    except ValidationError as exc:
        raise RuntimeError(error_message) from exc


async def intake_agent(llm_client: ILMUClient, complaint_text: str) -> IntakeResult:
    if not use_llm_agents():
        return _validated(IntakeResult, fallback_intake(complaint_text), "Fallback intake returned invalid data.")

    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
                prompt=f"Complaint:\n{complaint_text}",
                system=INTAKE_SYSTEM,
                max_tokens=256,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        payload = fallback_intake(complaint_text)
    if isinstance(payload.get("customer_name"), str):
        payload["customer_name"] = payload["customer_name"].strip() or None
    if isinstance(payload.get("order_id"), str):
        payload["order_id"] = payload["order_id"].strip().upper() or None
    if isinstance(payload.get("issue_type"), str):
        payload["issue_type"] = payload["issue_type"].strip().lower()
        issue_aliases = {
            "damaged": "damaged_item",
            "damage": "damaged_item",
            "broken": "damaged_item",
            "wrong": "wrong_item",
            "incorrect": "wrong_item",
            "late": "delivery_delay",
            "delayed": "delivery_delay",
        }
        payload["issue_type"] = issue_aliases.get(payload["issue_type"], payload["issue_type"])
    if isinstance(payload.get("sentiment"), str):
        payload["sentiment"] = payload["sentiment"].strip().lower()
    return _validated(IntakeResult, payload, "Intake agent returned invalid data.")


async def context_agent(
    llm_client: ILMUClient,
    data_manager: DataManager,
    intake: IntakeResult,
) -> ContextResult:
    order = data_manager.get_order(intake.order_id) if intake.order_id else None
    if not use_llm_agents():
        return _validated(ContextResult, fallback_context(intake, order), "Fallback context returned invalid data.")

    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
                prompt=(
                    f"Intake:\n{intake.model_dump_json(indent=2)}\n\n"
                    f"Order lookup result:\n{order if order is not None else 'null'}"
                ),
                system=CONTEXT_SYSTEM,
                max_tokens=256,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        payload = fallback_context(intake, order)
    payload["order_found"] = bool(order)
    payload["order_data"] = order
    return _validated(ContextResult, payload, "Context agent returned invalid data.")


async def reasoning_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    intake: IntakeResult,
    context: ContextResult,
) -> ReasoningResult:
    if not use_llm_agents():
        return _validated(
            ReasoningResult,
            fallback_reasoning(complaint_text, intake, context),
            "Fallback reasoning returned invalid data.",
        )

    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
                prompt=(
                    f"Complaint:\n{complaint_text}\n\n"
                    f"Intake:\n{intake.model_dump_json(indent=2)}\n\n"
                    f"Context:\n{context.model_dump_json(indent=2)}"
                ),
                system=REASONING_SYSTEM,
                max_tokens=1024,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        payload = fallback_reasoning(complaint_text, intake, context)
    if isinstance(payload.get("decision"), str):
        payload["decision"] = payload["decision"].strip().upper()
        decision_aliases = {
            "REPLACE": "RESHIP",
            "REPLACEMENT": "RESHIP",
            "DELIVERY_FOLLOW_UP": "RESHIP",
            "DELIVERY_FOLLOWUP": "RESHIP",
            "FOLLOW_UP": "RESHIP",
            "FOLLOWUP": "RESHIP",
            "MANUAL_REVIEW": "ESCALATE",
            "HUMAN_REVIEW": "ESCALATE",
            "ESCALATION": "ESCALATE",
            "REFUND_REQUEST": "REFUND",
        }
        payload["decision"] = decision_aliases.get(payload["decision"], payload["decision"])
        if payload["decision"] not in {"REFUND", "RESHIP", "ESCALATE", "DISMISS"}:
            payload = fallback_reasoning(complaint_text, intake, context)
    try:
        payload["confidence"] = max(0.0, min(1.0, float(payload.get("confidence", 0))))
    except (TypeError, ValueError):
        raise RuntimeError("Reasoning agent returned invalid confidence.")
    payload["requires_human_review"] = bool(payload.get("requires_human_review"))
    if isinstance(payload.get("rationale"), str):
        payload["rationale"] = payload["rationale"].strip()
    try:
        return _validated(ReasoningResult, payload, "Reasoning agent returned invalid data.")
    except RuntimeError:
        return _validated(
            ReasoningResult,
            fallback_reasoning(complaint_text, intake, context),
            "Fallback reasoning returned invalid data.",
        )


async def response_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    reasoning: ReasoningResult,
    context: ContextResult,
) -> ResponseResult:
    if not use_llm_agents():
        return _validated(
            ResponseResult,
            fallback_response(reasoning, context),
            "Fallback response returned invalid data.",
        )

    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
                prompt=(
                    f"Complaint:\n{complaint_text}\n\n"
                    f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\n"
                    f"Context:\n{context.model_dump_json(indent=2)}"
                ),
                system=RESPONSE_SYSTEM,
                max_tokens=1024,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        payload = fallback_response(reasoning, context)
    if isinstance(payload.get("english"), str):
        payload["english"] = payload["english"].strip()
    if isinstance(payload.get("bahasa_malaysia"), str):
        payload["bahasa_malaysia"] = payload["bahasa_malaysia"].strip()
    return _validated(ResponseResult, payload, "Response agent returned invalid data.")


async def supervisor_logic(
    llm_client: ILMUClient,
    reasoning: ReasoningResult,
    context: ContextResult,
) -> dict:
    if not use_llm_agents():
        return fallback_supervisor(reasoning, context)

    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
                prompt=(
                    f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\n"
                    f"Context:\n{context.model_dump_json(indent=2)}"
                ),
                system=SUPERVISOR_SYSTEM,
                max_tokens=256,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        payload = fallback_supervisor(reasoning, context)
    required_keys = {"requires_human_review", "priority", "supervisor_note"}
    if not required_keys.issubset(payload):
        payload = fallback_supervisor(reasoning, context)

    payload["requires_human_review"] = bool(payload["requires_human_review"])
    payload["priority"] = str(payload["priority"]).lower()
    if payload["priority"] not in {"normal", "high"}:
        payload["priority"] = "high" if payload["requires_human_review"] else "normal"
    payload["supervisor_note"] = str(payload["supervisor_note"]).strip()
    return payload


def fallback_intake(complaint_text: str) -> dict:
    lowered = complaint_text.lower()
    order_match = re.search(r"\b(?:ORD|KM)-\d+\b", complaint_text, flags=re.IGNORECASE)
    issue_type = "unknown"
    if any(word in lowered for word in ("damaged", "broken", "torn", "rosak", "koyak")):
        issue_type = "damaged_item"
    elif any(word in lowered for word in ("wrong", "incorrect", "salah")):
        issue_type = "wrong_item"
    elif any(word in lowered for word in ("late", "delay", "where is", "tracking", "lambat")):
        issue_type = "delivery_delay"
    elif "refund" in lowered:
        issue_type = "refund_request"
    sentiment = "negative" if issue_type != "unknown" or any(
        word in lowered for word in ("angry", "bad", "upset", "disappointed", "frustrated")
    ) else "neutral"
    return {
        "customer_name": None,
        "order_id": order_match.group(0).upper() if order_match else None,
        "issue_type": issue_type,
        "sentiment": sentiment,
    }


def fallback_context(intake: IntakeResult, order: dict | None) -> dict:
    if order:
        return {
            "order_found": True,
            "order_data": order,
            "notes": (
                f"Order found for {order.get('customer_name', 'customer')}. "
                f"Status: {order.get('status', 'UNKNOWN')}. Issue: {intake.issue_type}."
            ),
        }
    if intake.order_id:
        notes = f"Order ID {intake.order_id} was provided, but no matching order was found."
    else:
        notes = "No order ID was provided, so the order could not be located."
    return {"order_found": False, "order_data": None, "notes": notes}


def fallback_reasoning(
    complaint_text: str,
    intake: IntakeResult,
    context: ContextResult,
) -> dict:
    if not context.order_found:
        return {
            "decision": "ESCALATE",
            "confidence": 0.9,
            "rationale": "Order context is missing, so a support agent should verify the customer and order details.",
            "requires_human_review": True,
        }
    if intake.issue_type == "damaged_item":
        return {
            "decision": "REFUND",
            "confidence": 0.9,
            "rationale": "The customer reports a damaged item for an order that exists in the system.",
            "requires_human_review": False,
        }
    if intake.issue_type in {"wrong_item", "delivery_delay"}:
        return {
            "decision": "RESHIP",
            "confidence": 0.82,
            "rationale": "The issue can likely be resolved by arranging a replacement or delivery follow-up.",
            "requires_human_review": False,
        }
    return {
        "decision": "ESCALATE",
        "confidence": 0.65,
        "rationale": "The complaint is not specific enough for an automated decision.",
        "requires_human_review": True,
    }


def fallback_response(reasoning: ReasoningResult, context: ContextResult) -> dict:
    order = context.order_data or {}
    name = order.get("customer_name") or "there"
    item = order.get("item") or "your item"
    amount = ""
    if order.get("total") and order.get("currency"):
        amount = f" {order['currency']} {float(order['total']):.2f}"

    if reasoning.decision == "REFUND":
        english = (
            f"Hi {name}, we are sorry that {item} arrived damaged. "
            f"We have approved a refund{amount} to your original payment method. "
            "Please allow a few business days for it to appear."
        )
        bahasa = (
            f"Hai {name}, kami mohon maaf kerana {item} tiba dalam keadaan rosak. "
            f"Kami telah meluluskan bayaran balik{amount} ke kaedah pembayaran asal anda. "
            "Sila berikan beberapa hari bekerja untuk ia dipaparkan."
        )
    elif reasoning.decision == "RESHIP":
        english = (
            f"Hi {name}, we are sorry for the issue with {item}. "
            "We will arrange a replacement or delivery follow-up and update you shortly."
        )
        bahasa = (
            f"Hai {name}, kami mohon maaf atas isu berkaitan {item}. "
            "Kami akan mengatur penggantian atau semakan penghantaran dan mengemas kini anda tidak lama lagi."
        )
    else:
        english = (
            "Hi there, we could not confidently resolve this automatically. "
            "We have escalated your case to our support team for review."
        )
        bahasa = (
            "Hai, kami tidak dapat menyelesaikan isu ini secara automatik dengan yakin. "
            "Kes anda telah diserahkan kepada pasukan sokongan untuk semakan."
        )
    return {"english": english, "bahasa_malaysia": bahasa}


def fallback_supervisor(reasoning: ReasoningResult, context: ContextResult) -> dict:
    requires_review = reasoning.requires_human_review or not context.order_found
    return {
        "requires_human_review": requires_review,
        "priority": "high" if requires_review else "normal",
        "supervisor_note": "Fallback supervisor logic used because structured LLM output was unavailable.",
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
