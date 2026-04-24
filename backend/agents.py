from __future__ import annotations

import asyncio
import re
from uuid import uuid4

import httpx
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

AGENT_LLM_TIMEOUT_SECONDS = 12


def _validated(model_cls, payload: dict, fallback_message: str):
    try:
        return model_cls(**payload)
    except ValidationError as exc:
        raise RuntimeError(fallback_message) from exc


def _extract_order_id(text: str) -> str | None:
    match = re.search(r"\b([A-Z]{2,5}-\d{3,6})\b", text.upper())
    return match.group(1) if match else None


def _fallback_intake(complaint_text: str) -> dict:
    lowered = complaint_text.lower()
    if any(word in lowered for word in ("damage", "damaged", "broken", "crack", "rosak", "pecah", "torn")):
        issue_type = "damaged_item"
    elif any(word in lowered for word in ("wrong item", "incorrect item", "salah barang", "missing item")):
        issue_type = "wrong_item"
    elif any(word in lowered for word in ("late", "delay", "tak sampai", "not arrive", "still processing")):
        issue_type = "delivery_delay"
    elif any(word in lowered for word in ("refund", "money back", "bayaran balik")):
        issue_type = "refund_request"
    elif any(word in lowered for word in ("bill", "charged", "payment", "billing")):
        issue_type = "billing"
    else:
        issue_type = "unknown"

    if any(word in lowered for word in ("angry", "terrible", "bad", "refund", "rosak", "broken", "late")):
        sentiment = "negative"
    elif any(word in lowered for word in ("thanks", "thank you", "please")):
        sentiment = "positive"
    else:
        sentiment = "neutral"

    return {
        "customer_name": None,
        "order_id": _extract_order_id(complaint_text),
        "issue_type": issue_type,
        "sentiment": sentiment,
    }


def _fallback_context(order: dict | None, intake: IntakeResult) -> dict:
    if order:
        notes = f"Order found for {order.get('status', 'unknown').lower()} item."
    elif intake.order_id:
        notes = "Order ID provided but no matching order was found."
    else:
        notes = "Missing order ID. Ask user to provide an order ID."
    return {
        "order_found": bool(order),
        "order_data": order,
        "notes": notes,
    }


def _fallback_reasoning(intake: IntakeResult, context: ContextResult) -> dict:
    if not context.order_found:
        return {
            "decision": "ESCALATE",
            "confidence": 0.35,
            "rationale": "We could not verify the order details automatically.",
            "requires_human_review": True,
        }
    if intake.issue_type == "damaged_item":
        return {
            "decision": "REFUND",
            "confidence": 0.86,
            "rationale": "The complaint indicates the delivered item arrived damaged.",
            "requires_human_review": False,
        }
    if intake.issue_type in {"wrong_item", "delivery_delay"}:
        return {
            "decision": "RESHIP",
            "confidence": 0.78,
            "rationale": "A replacement is the fastest resolution for this delivery issue.",
            "requires_human_review": False,
        }
    if intake.issue_type in {"billing", "refund_request"}:
        return {
            "decision": "ESCALATE",
            "confidence": 0.6,
            "rationale": "Billing and refund requests need manual verification before action.",
            "requires_human_review": True,
        }
    return {
        "decision": "ESCALATE",
        "confidence": 0.5,
        "rationale": "The case needs manual review because the issue is still unclear.",
        "requires_human_review": True,
    }


def _fallback_response(reasoning: ReasoningResult, context: ContextResult) -> dict:
    item = context.order_data.get("item") if context.order_data else "your order"
    if reasoning.decision == "REFUND":
        english = f"Thanks for reaching out. We are sorry that {item} arrived damaged. We will proceed with a refund for you."
        bahasa_malaysia = f"Terima kasih kerana menghubungi kami. Kami mohon maaf kerana {item} tiba dalam keadaan rosak. Kami akan teruskan proses bayaran balik untuk anda."
    elif reasoning.decision == "RESHIP":
        english = f"Thanks for reaching out. We will arrange a replacement for {item} and keep you updated."
        bahasa_malaysia = f"Terima kasih kerana menghubungi kami. Kami akan aturkan penggantian untuk {item} dan memaklumkan perkembangan kepada anda."
    elif reasoning.decision == "DISMISS":
        english = "Thanks for reaching out. Based on the current order details, we could not confirm an issue that needs action."
        bahasa_malaysia = "Terima kasih kerana menghubungi kami. Berdasarkan butiran pesanan semasa, kami tidak dapat mengesahkan isu yang memerlukan tindakan."
    else:
        english = "Thanks for reaching out. We need a support specialist to review this case before we take action."
        bahasa_malaysia = "Terima kasih kerana menghubungi kami. Kami memerlukan pegawai sokongan untuk menyemak kes ini sebelum tindakan diambil."
    return {
        "english": english,
        "bahasa_malaysia": bahasa_malaysia,
    }


def _fallback_supervisor(reasoning: ReasoningResult, context: ContextResult) -> dict:
    needs_review = reasoning.requires_human_review or not context.order_found
    return {
        "requires_human_review": needs_review,
        "priority": "high" if needs_review else "normal",
        "supervisor_note": (
            "Escalate to human support for manual handling."
            if needs_review
            else "Auto-resolution is acceptable."
        ),
    }


async def intake_agent(llm_client: ILMUClient, complaint_text: str) -> IntakeResult:
    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
            prompt=f"Complaint:\n{complaint_text}",
            system=INTAKE_SYSTEM,
            max_tokens=220,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except (RuntimeError, httpx.HTTPError, TimeoutError):
        payload = _fallback_intake(complaint_text)
    if isinstance(payload.get("customer_name"), str):
        payload["customer_name"] = payload["customer_name"].strip() or None
    if isinstance(payload.get("order_id"), str):
        payload["order_id"] = payload["order_id"].strip().upper() or None
    if isinstance(payload.get("issue_type"), str):
        payload["issue_type"] = payload["issue_type"].strip().lower()
    if isinstance(payload.get("sentiment"), str):
        payload["sentiment"] = payload["sentiment"].strip().lower()
    return _validated(IntakeResult, payload, "Intake agent returned invalid data.")


async def context_agent(
    llm_client: ILMUClient,
    data_manager: DataManager,
    intake: IntakeResult,
) -> ContextResult:
    order = data_manager.get_order(intake.order_id) if intake.order_id else None
    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
            prompt=(
                f"Intake:\n{intake.model_dump_json(indent=2)}\n\n"
                f"Order lookup result:\n{order if order is not None else 'null'}"
            ),
            system=CONTEXT_SYSTEM,
            max_tokens=180,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except (RuntimeError, httpx.HTTPError, TimeoutError):
        payload = _fallback_context(order, intake)
    payload["order_found"] = bool(order)
    payload["order_data"] = order
    return _validated(ContextResult, payload, "Context agent returned invalid data.")


async def reasoning_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    intake: IntakeResult,
    context: ContextResult,
) -> ReasoningResult:
    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
            prompt=(
                f"Complaint:\n{complaint_text}\n\n"
                f"Intake:\n{intake.model_dump_json(indent=2)}\n\n"
                f"Context:\n{context.model_dump_json(indent=2)}"
            ),
            system=REASONING_SYSTEM,
            max_tokens=260,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except (RuntimeError, httpx.HTTPError, TimeoutError):
        payload = _fallback_reasoning(intake, context)
    if isinstance(payload.get("decision"), str):
        payload["decision"] = payload["decision"].strip().upper()
    try:
        payload["confidence"] = max(0.0, min(1.0, float(payload.get("confidence", 0))))
    except (TypeError, ValueError):
        raise RuntimeError("Reasoning agent returned invalid confidence.")
    payload["requires_human_review"] = bool(payload.get("requires_human_review"))
    if isinstance(payload.get("rationale"), str):
        payload["rationale"] = payload["rationale"].strip()
    return _validated(ReasoningResult, payload, "Reasoning agent returned invalid data.")


async def response_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    reasoning: ReasoningResult,
    context: ContextResult,
) -> ResponseResult:
    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
            prompt=(
                f"Complaint:\n{complaint_text}\n\n"
                f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\n"
                f"Context:\n{context.model_dump_json(indent=2)}"
            ),
            system=RESPONSE_SYSTEM,
            max_tokens=320,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except (RuntimeError, httpx.HTTPError, TimeoutError):
        payload = _fallback_response(reasoning, context)
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
    try:
        payload = await asyncio.wait_for(
            llm_client.chat_json(
            prompt=(
                f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\n"
                f"Context:\n{context.model_dump_json(indent=2)}"
            ),
            system=SUPERVISOR_SYSTEM,
            max_tokens=180,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except (RuntimeError, httpx.HTTPError, TimeoutError):
        payload = _fallback_supervisor(reasoning, context)
    required_keys = {"requires_human_review", "priority", "supervisor_note"}
    if not required_keys.issubset(payload):
        raise RuntimeError("Supervisor agent returned invalid data.")

    payload["requires_human_review"] = bool(payload["requires_human_review"])
    payload["priority"] = str(payload["priority"]).lower()
    if payload["priority"] not in {"normal", "high"}:
        payload["priority"] = "high" if payload["requires_human_review"] else "normal"
    payload["supervisor_note"] = str(payload["supervisor_note"]).strip()
    return payload


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
