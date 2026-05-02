from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import date, datetime
from uuid import uuid4

from pydantic import ValidationError

from backend.llm import ILMUClient, estimate_tokens
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
- language: one of "EN", "BM", "Manglish"
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
_DEFAULT_REASONING_EFFORT = object()
ORDER_ID_PATTERN = re.compile(r"\b(?:ORD|KM)-\d+\b", flags=re.IGNORECASE)


def use_llm_agents() -> bool:
    return os.getenv("USE_LLM_AGENTS", "true").lower() in {"1", "true", "yes", "on"}


def _validated(model_cls, payload: dict, error_message: str):
    try:
        return model_cls(**payload)
    except ValidationError as exc:
        raise RuntimeError(error_message) from exc


def _record_usage(metrics: dict | None, usage: dict) -> None:
    if metrics is None:
        return
    # Agent metrics are accumulated per LLM call so fallback clients remain compatible.
    metrics["input_tokens"] = int(metrics.get("input_tokens", 0)) + int(usage.get("input_tokens", 0))
    metrics["output_tokens"] = int(metrics.get("output_tokens", 0)) + int(usage.get("output_tokens", 0))
    if "provider_used" in usage:
        metrics["provider_used"] = usage["provider_used"]
    if "fallback_used" in usage:
        metrics["fallback_used"] = bool(usage["fallback_used"])
    if usage.get("fallback_reason"):
        metrics["fallback_reason"] = usage["fallback_reason"]


def _mark_execution_mode(metrics: dict | None, mode: str) -> None:
    if metrics is not None:
        metrics["execution_mode"] = mode


def extract_order_id(text: str) -> str | None:
    match = ORDER_ID_PATTERN.search(text)
    return match.group(0).upper() if match else None


def _should_auto_reship_wrong_item(intake: IntakeResult, context: ContextResult) -> bool:
    return bool(context.order_found and intake.issue_type == "wrong_item")


def _days_since_delivery(order: dict) -> int | None:
    raw_date = order.get("delivery_date")
    if not raw_date:
        return None
    try:
        delivered_at = datetime.fromisoformat(str(raw_date)).date()
    except ValueError:
        return None
    return (date.today() - delivered_at).days


def _should_dismiss_refund_request(complaint_text: str, intake: IntakeResult, context: ContextResult) -> bool:
    if not context.order_found or not context.order_data:
        return False
    lowered = complaint_text.lower()
    order = context.order_data
    refund_window = int(order.get("seller_policy_refund_days") or 30)
    days_since_delivery = _days_since_delivery(order)
    outside_window = days_since_delivery is not None and days_since_delivery > refund_window
    change_of_mind = any(
        phrase in lowered
        for phrase in (
            "changed my mind",
            "change of mind",
            "don't want it",
            "do not want it",
            "used them",
            "used it",
            "45 days",
            "outside return window",
        )
    )
    no_defect_claimed = any(
        phrase in lowered
        for phrase in (
            "nothing wrong",
            "not damaged",
            "fit fine",
            "works fine",
            "no issue",
        )
    )
    return bool(intake.issue_type == "refund_request" and outside_window and (change_of_mind or no_defect_claimed))


def _is_high_confidence_automated_resolution(reasoning: ReasoningResult, context: ContextResult) -> bool:
    return bool(
        context.order_found
        and reasoning.decision in {"REFUND", "RESHIP"}
        and reasoning.confidence >= 0.8
        and not reasoning.requires_human_review
    )


async def _chat_json_with_metrics(
    llm_client: ILMUClient,
    *,
    prompt: str,
    system: str,
    metrics: dict | None,
    max_tokens: int | None = None,
    reasoning_effort=_DEFAULT_REASONING_EFFORT,
) -> dict:
    chat_kwargs = {"system": system, "max_tokens": max_tokens}
    if reasoning_effort is not _DEFAULT_REASONING_EFFORT:
        chat_kwargs["reasoning_effort"] = reasoning_effort

    if metrics is None or not hasattr(llm_client, "chat_json_with_usage"):
        payload = await llm_client.chat_json(prompt, **chat_kwargs)
        if metrics is not None:
            usage = {
                "input_tokens": estimate_tokens(f"{system}\n{prompt}"),
                "output_tokens": estimate_tokens(json.dumps(payload, ensure_ascii=False)),
            }
            _record_usage(metrics, usage)
            _mark_execution_mode(metrics, "llm")
        return payload

    payload, usage = await llm_client.chat_json_with_usage(prompt, **chat_kwargs)
    _record_usage(metrics, usage)
    _mark_execution_mode(metrics, "fallback" if usage.get("fallback_used") else "llm")
    return payload


async def intake_agent(llm_client: ILMUClient, complaint_text: str, metrics: dict | None = None) -> IntakeResult:
    if not use_llm_agents():
        _mark_execution_mode(metrics, "fallback")
        return _validated(IntakeResult, fallback_intake(complaint_text), "Fallback intake returned invalid data.")

    prompt = f"Complaint:\n{complaint_text}"
    try:
        payload = await asyncio.wait_for(
            _chat_json_with_metrics(
                llm_client,
                prompt=prompt,
                system=INTAKE_SYSTEM,
                metrics=metrics,
                max_tokens=256,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        _mark_execution_mode(metrics, "fallback")
        payload = fallback_intake(complaint_text)
    if isinstance(payload.get("customer_name"), str):
        payload["customer_name"] = payload["customer_name"].strip() or None
    if isinstance(payload.get("order_id"), str):
        payload["order_id"] = payload["order_id"].strip().upper() or None
    if not payload.get("order_id"):
        payload["order_id"] = extract_order_id(complaint_text)
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
    payload["language"] = normalize_language(payload.get("language"), complaint_text)
    return _validated(IntakeResult, payload, "Intake agent returned invalid data.")


async def context_agent(
    llm_client: ILMUClient,
    data_manager: DataManager,
    intake: IntakeResult,
    metrics: dict | None = None,
) -> ContextResult:
    order = data_manager.get_order(intake.order_id) if intake.order_id else None
    if not use_llm_agents():
        _mark_execution_mode(metrics, "fallback")
        return _validated(ContextResult, fallback_context(intake, order), "Fallback context returned invalid data.")

    prompt = (
        f"Intake:\n{intake.model_dump_json(indent=2)}\n\nOrder lookup result:\n{order if order is not None else 'null'}"
    )
    try:
        payload = await asyncio.wait_for(
            _chat_json_with_metrics(
                llm_client,
                prompt=prompt,
                system=CONTEXT_SYSTEM,
                metrics=metrics,
                max_tokens=256,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        _mark_execution_mode(metrics, "fallback")
        payload = fallback_context(intake, order)
    payload["order_found"] = bool(order)
    payload["order_data"] = order
    return _validated(ContextResult, payload, "Context agent returned invalid data.")


async def reasoning_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    intake: IntakeResult,
    context: ContextResult,
    metrics: dict | None = None,
) -> ReasoningResult:
    if not use_llm_agents():
        _mark_execution_mode(metrics, "fallback")
        return _validated(
            ReasoningResult,
            fallback_reasoning(complaint_text, intake, context),
            "Fallback reasoning returned invalid data.",
        )

    prompt = (
        f"Complaint:\n{complaint_text}\n\n"
        f"Intake:\n{intake.model_dump_json(indent=2)}\n\n"
        f"Context:\n{context.model_dump_json(indent=2)}"
    )
    try:
        payload = await asyncio.wait_for(
            _chat_json_with_metrics(
                llm_client,
                prompt=prompt,
                system=REASONING_SYSTEM,
                metrics=metrics,
                max_tokens=1024,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        _mark_execution_mode(metrics, "fallback")
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
            _mark_execution_mode(metrics, "fallback")
            payload = fallback_reasoning(complaint_text, intake, context)
    try:
        payload["confidence"] = max(0.0, min(1.0, float(payload.get("confidence", 0))))
    except (TypeError, ValueError):
        raise RuntimeError("Reasoning agent returned invalid confidence.")
    payload["requires_human_review"] = bool(payload.get("requires_human_review"))
    if _should_auto_reship_wrong_item(intake, context):
        payload["decision"] = "RESHIP"
        payload["requires_human_review"] = False
        payload["confidence"] = max(payload["confidence"], 0.82)
        if not payload.get("rationale") or "manual" in str(payload.get("rationale")).lower():
            payload["rationale"] = (
                "Wrong item reported for an order found in the system; replacement is the preferred policy path."
            )
    if _should_dismiss_refund_request(complaint_text, intake, context):
        payload["decision"] = "DISMISS"
        payload["requires_human_review"] = False
        payload["confidence"] = max(payload["confidence"], 0.9)
        payload["rationale"] = (
            "Change-of-mind refund request is outside the seller refund window and no damage or fulfillment issue is claimed."
        )
    if isinstance(payload.get("rationale"), str):
        payload["rationale"] = payload["rationale"].strip()
    try:
        return _validated(ReasoningResult, payload, "Reasoning agent returned invalid data.")
    except RuntimeError:
        _mark_execution_mode(metrics, "fallback")
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
    metrics: dict | None = None,
) -> ResponseResult:
    if not use_llm_agents():
        _mark_execution_mode(metrics, "fallback")
        return _validated(
            ResponseResult,
            fallback_response(reasoning, context),
            "Fallback response returned invalid data.",
        )

    prompt = (
        f"Complaint:\n{complaint_text}\n\n"
        f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\n"
        f"Context:\n{context.model_dump_json(indent=2)}"
    )
    try:
        payload = await asyncio.wait_for(
            _chat_json_with_metrics(
                llm_client,
                prompt=prompt,
                system=RESPONSE_SYSTEM,
                metrics=metrics,
                max_tokens=1024,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        _mark_execution_mode(metrics, "fallback")
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
    metrics: dict | None = None,
) -> dict:
    if not use_llm_agents():
        _mark_execution_mode(metrics, "fallback")
        return fallback_supervisor(reasoning, context)

    prompt = f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\nContext:\n{context.model_dump_json(indent=2)}"
    try:
        payload = await asyncio.wait_for(
            _chat_json_with_metrics(
                llm_client,
                prompt=prompt,
                system=SUPERVISOR_SYSTEM,
                metrics=metrics,
                max_tokens=256,
                reasoning_effort=None,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        _mark_execution_mode(metrics, "fallback")
        payload = fallback_supervisor(reasoning, context)
    required_keys = {"requires_human_review", "priority", "supervisor_note"}
    if not required_keys.issubset(payload):
        _mark_execution_mode(metrics, "fallback")
        payload = fallback_supervisor(reasoning, context)

    payload["requires_human_review"] = bool(payload["requires_human_review"])
    payload["priority"] = str(payload["priority"]).lower()
    if payload["priority"] not in {"normal", "high"}:
        payload["priority"] = "high" if payload["requires_human_review"] else "normal"
    payload["supervisor_note"] = str(payload["supervisor_note"]).strip()
    if _is_high_confidence_automated_resolution(reasoning, context):
        payload["requires_human_review"] = False
        payload["priority"] = "normal"
        if not payload["supervisor_note"] or "manual" in payload["supervisor_note"].lower():
            payload["supervisor_note"] = "High-confidence automated resolution; no manual review required."
    return payload


def fallback_intake(complaint_text: str) -> dict:
    lowered = complaint_text.lower()
    issue_type = "unknown"
    if any(word in lowered for word in ("damaged", "broken", "torn", "rosak", "koyak")):
        issue_type = "damaged_item"
    elif any(word in lowered for word in ("wrong", "incorrect", "salah")):
        issue_type = "wrong_item"
    elif any(word in lowered for word in ("late", "delay", "where is", "tracking", "lambat")):
        issue_type = "delivery_delay"
    elif "refund" in lowered:
        issue_type = "refund_request"
    sentiment = (
        "negative"
        if issue_type != "unknown"
        or any(word in lowered for word in ("angry", "bad", "upset", "disappointed", "frustrated"))
        else "neutral"
    )
    return {
        "customer_name": None,
        "order_id": extract_order_id(complaint_text),
        "issue_type": issue_type,
        "sentiment": sentiment,
        "language": detect_language(complaint_text),
    }


def detect_language(text: str) -> str:
    lowered = text.lower()
    bm_pattern = r"\b(saya|barang|tak|lagi|nak|pesanan|terima kasih|rosak|lambat|salah|bayaran balik)\b"
    en_pattern = r"\b(order|tracking|refund|processing|delivered|damaged|replacement|delay)\b"
    has_bm = bool(re.search(bm_pattern, lowered))
    has_en = bool(re.search(en_pattern, lowered))
    if has_bm and has_en:
        return "Manglish"
    if has_bm:
        return "BM"
    return "EN"


def normalize_language(value, complaint_text: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return detect_language(complaint_text)
    normalized = value.strip().lower().replace("_", " ").replace("-", " ")
    if normalized in {"en", "eng", "english"}:
        return "EN"
    if normalized in {"bm", "bahasa", "bahasa malaysia", "malay", "ms"}:
        return "BM"
    if normalized in {"manglish", "mixed", "mixed bm en", "bm en", "english malay", "malay english"}:
        return "Manglish"
    return detect_language(complaint_text)


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
    if _should_dismiss_refund_request(complaint_text, intake, context):
        return {
            "decision": "DISMISS",
            "confidence": 0.9,
            "rationale": "The customer is requesting a change-of-mind refund outside the seller refund window, with no damage or fulfillment issue claimed.",
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
    elif reasoning.decision == "DISMISS":
        english = (
            f"Hi {name}, thanks for contacting us about {item}. "
            "We checked the order and this refund request is outside the seller return window. "
            "Because no damage or fulfillment issue was reported, we are unable to approve a refund for this order."
        )
        bahasa = (
            f"Hai {name}, terima kasih kerana menghubungi kami tentang {item}. "
            "Kami telah menyemak pesanan ini dan permintaan bayaran balik berada di luar tempoh pemulangan penjual. "
            "Memandangkan tiada kerosakan atau isu penghantaran dilaporkan, kami tidak dapat meluluskan bayaran balik untuk pesanan ini."
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


def build_event(
    complaint_id: str,
    step: str,
    message: str,
    payload: dict | None = None,
    metrics: dict | None = None,
) -> dict:
    from datetime import datetime, timezone

    event = {
        "id": str(uuid4()),
        "complaint_id": complaint_id,
        "step": step,
        "message": message,
        "payload": payload or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if metrics:
        event.update(
            {
                "agent": metrics.get("agent", step),
                "duration": metrics.get("duration", 0.0),
                "input_tokens": metrics.get("input_tokens", 0),
                "output_tokens": metrics.get("output_tokens", 0),
                "execution_mode": metrics.get("execution_mode", "unknown"),
            }
        )
        for key in ("provider_used", "fallback_used", "fallback_reason"):
            if key in metrics:
                event[key] = metrics[key]
    return event
