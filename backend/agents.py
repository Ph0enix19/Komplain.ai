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
    ImageAnalysisResult,
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

VISION_INSPECTION_SYSTEM = """You are the visual evidence agent for an e-commerce complaints workflow.
Inspect the uploaded customer image and compare it with the complaint and order context.
Return only valid JSON with exactly these keys:
- image_provided: boolean
- image_analyzed: boolean
- item_visible: boolean or null
- package_visible: boolean or null
- damage_detected: boolean or null
- damage_level: one of "none", "minor", "moderate", "major", "unknown"
- damage_type: short string or null
- matches_order_item: boolean or null
- matched_order_item: short string or null
- confidence: number between 0 and 1
- evidence: short string
- human_review_required: boolean
Avoid overclaiming. Use human_review_required=true when the image is unclear, confidence is low, or the visible item/package does not match the order."""

REASONING_SYSTEM = """You are the reasoning agent for a customer complaints workflow.
Decide the next action using the provided complaint, intake, order context, and optional visual evidence.
The complaint can be English, Bahasa Malaysia, or Manglish, but every field you output must be English only.
Return only valid JSON with exactly these keys:
- decision: one of "REFUND", "RESHIP", "CLARIFY", "ESCALATE", "DISMISS"
- confidence: number between 0 and 1
- rationale: short string
- requires_human_review: boolean
- clarification_needed: boolean
- clarification_message: string or null
Prefer REFUND for clearly damaged delivered items.
Prefer RESHIP for wrong item or delivery delay when a replacement is appropriate.
Use visual evidence as supporting evidence, not the only source of truth.
Use CLARIFY when the seller needs more customer information before deciding refund, reship, dismissal, or escalation.
If the complaint says the order is missing but visual evidence shows a package/item was received, set clarification_needed=true, decision=CLARIFY, and ask the customer to confirm whether the package was received or is still missing.
If visual evidence conflicts with the complaint, prefer ESCALATE or human review unless the order policy is unambiguous.
Use ESCALATE when the order is missing, unclear, risky, or needs manual review."""

RESPONSE_SYSTEM = """You are the response agent for a customer complaints workflow.
Draft customer-facing replies based on the complaint, decision, and order context.
Return only valid JSON with exactly these keys:
- english: string
- bahasa_malaysia: string
Use the customer_name from context.order_data when it is present and looks like a real customer name.
Do not invent customer names and do not use placeholder names like "Demo Customer".
If no real customer name is available, use a neutral greeting like "Hi there".
If reasoning.clarification_needed is true, do not offer refund or reship yet. Politely mention the contradiction and ask the customer to confirm the missing vs received package status.
Keep the message concise, empathetic, and aligned with the decision."""

SUPERVISOR_SYSTEM = """You are the supervisor agent for a customer complaints workflow.
Review the reasoning result for the seller/support operator, not for the customer.
The input can include English, Bahasa Malaysia, or Manglish, but supervisor_note must be English only and seller-facing.
Return only valid JSON with exactly these keys:
- requires_human_review: boolean
- priority: one of "normal", "high"
- supervisor_note: short English seller-facing instruction"""

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


def _normalized_image_analysis(payload: dict) -> dict:
    payload = dict(payload or {})
    payload.setdefault("image_provided", True)
    payload.setdefault("image_analyzed", False)
    payload.setdefault("item_visible", None)
    payload.setdefault("package_visible", None)
    payload.setdefault("damage_detected", None)
    payload.setdefault("damage_level", "unknown")
    payload.setdefault("damage_type", None)
    payload.setdefault("matches_order_item", None)
    payload.setdefault("matched_order_item", None)
    payload.setdefault("confidence", 0)
    payload.setdefault(
        "evidence",
        "Image could not be analyzed. Decision should rely on complaint text and order context.",
    )
    payload.setdefault("human_review_required", True)

    damage_level = str(payload.get("damage_level") or "unknown").strip().lower()
    if damage_level not in {"none", "minor", "moderate", "major", "unknown"}:
        damage_level = "unknown"
    payload["damage_level"] = damage_level
    try:
        payload["confidence"] = max(0.0, min(1.0, float(payload.get("confidence", 0))))
    except (TypeError, ValueError):
        payload["confidence"] = 0
    payload["human_review_required"] = bool(payload.get("human_review_required"))
    if payload["confidence"] < 0.65:
        payload["human_review_required"] = True
    return payload


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


def _contains_malay_markers(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    markers = (
        "saya",
        "barang",
        "pesanan",
        "bayaran balik",
        "rosak",
        "koyak",
        "tak ",
        "tidak ",
        "belum",
        "sampai",
        "pelanggan",
        "memerlukan",
        "semakan",
        "dihantar",
        "diterima",
        "bungkusan",
    )
    return any(marker in lowered for marker in markers)


def _english_supervisor_note(reasoning: ReasoningResult, context: ContextResult) -> str:
    if reasoning.clarification_needed:
        return "Seller action: request customer clarification before approving refund, reship, or dismissal."
    if reasoning.requires_human_review or not context.order_found:
        return "Seller action: review the case manually because the order context or evidence is incomplete."
    return "Seller action: automated resolution is acceptable based on the current order context and reasoning result."


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


def _is_missing_order_claim(complaint_text: str, intake: IntakeResult) -> bool:
    lowered = complaint_text.lower()
    missing_markers = (
        "order is missing",
        "package is missing",
        "parcel is missing",
        "item is missing",
        "missing order",
        "missing package",
        "missing parcel",
        "not received",
        "never received",
        "didn't receive",
        "did not receive",
        "where is it",
        "where is my order",
        "tak sampai",
        "belum sampai",
        "hilang",
    )
    return bool(intake.issue_type == "delivery_delay" and any(marker in lowered for marker in missing_markers))


def _visual_evidence_shows_received_package(image_analysis: ImageAnalysisResult | None) -> bool:
    if not image_analysis or not image_analysis.image_analyzed or image_analysis.confidence < 0.7:
        return False
    return bool(
        image_analysis.package_visible is True
        or image_analysis.item_visible is True
        or image_analysis.damage_detected is True
        or image_analysis.damage_level in {"minor", "moderate", "major"}
    )


def _missing_claim_contradiction(
    complaint_text: str,
    intake: IntakeResult,
    image_analysis: ImageAnalysisResult | None,
) -> bool:
    return _is_missing_order_claim(complaint_text, intake) and _visual_evidence_shows_received_package(image_analysis)


def _missing_package_clarification_message() -> str:
    return "Please confirm whether you received the package or whether the order is still missing."


def _evidence_mismatch_clarification_message() -> str:
    return "Please confirm the issue and upload a clear photo of the damaged item or packaging if available."


def _clarification_message() -> str:
    return "Please confirm the issue so the seller can review the correct next step."


def _customer_safe_clarification_message(message: str | None, customer_name: str | None = None) -> str:
    if not message:
        return _clarification_message()
    stripped = message.strip()
    lowered = stripped.lower()
    unsafe_markers = ("hi ", "hello", "thank you", "thanks for", "dear ")
    if any(marker in lowered for marker in unsafe_markers):
        return _clarification_message()
    if customer_name and customer_name.lower() in lowered:
        return _clarification_message()
    return stripped


PLACEHOLDER_CUSTOMER_NAMES = {
    "customer",
    "demo customer",
    "test customer",
    "live demo customer",
}


def _context_customer_name(context: ContextResult) -> str | None:
    raw_name = (context.order_data or {}).get("customer_name")
    if not isinstance(raw_name, str):
        return None
    name = raw_name.strip()
    if not name or name.lower() in PLACEHOLDER_CUSTOMER_NAMES:
        return None
    return name


def _sanitize_response_customer_names(payload: dict, context: ContextResult) -> dict:
    name = _context_customer_name(context)
    replacement = name or "there"
    for key in ("english", "bahasa_malaysia"):
        if isinstance(payload.get(key), str):
            for placeholder in ("Demo Customer", "Test Customer", "Live Demo Customer"):
                payload[key] = payload[key].replace(placeholder, replacement)
    return payload


def _is_high_confidence_automated_resolution(reasoning: ReasoningResult, context: ContextResult) -> bool:
    return bool(
        context.order_found
        and reasoning.decision in {"REFUND", "RESHIP"}
        and reasoning.confidence >= 0.8
        and not reasoning.requires_human_review
        and not reasoning.clarification_needed
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


async def vision_inspection_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    context: ContextResult,
    image_path: str | None,
    metrics: dict | None = None,
) -> ImageAnalysisResult:
    if not image_path:
        _mark_execution_mode(metrics, "skipped")
        return ImageAnalysisResult()

    fallback_payload = fallback_image_analysis(image_provided=True)
    if os.getenv("VISION_ENABLED", "true").lower() not in {"1", "true", "yes", "on"}:
        _mark_execution_mode(metrics, "fallback")
        fallback_payload["evidence"] = "Vision analysis is disabled. Decision should rely on complaint text and order context."
        return _validated(ImageAnalysisResult, fallback_payload, "Fallback image analysis returned invalid data.")

    order = context.order_data or {}
    prompt = (
        f"Complaint:\n{complaint_text}\n\n"
        f"Order context:\n{json.dumps(order, ensure_ascii=False)}\n\n"
        "Inspect the image for visible item or packaging damage. "
        "Compare the visible item/package with the order item/category when possible."
    )
    try:
        if not hasattr(llm_client, "chat_json_with_image"):
            raise RuntimeError("Configured LLM client does not support image input.")
        payload = await asyncio.wait_for(
            llm_client.chat_json_with_image(
                image_path,
                prompt,
                VISION_INSPECTION_SYSTEM,
                max_tokens=512,
            ),
            timeout=AGENT_LLM_TIMEOUT_SECONDS,
        )
        payload = _normalized_image_analysis(payload)
        payload["image_provided"] = True
        payload["image_analyzed"] = True
        if metrics is not None:
            _record_usage(
                metrics,
                {
                    "input_tokens": estimate_tokens(f"{VISION_INSPECTION_SYSTEM}\n{prompt}"),
                    "output_tokens": estimate_tokens(json.dumps(payload, ensure_ascii=False)),
                    "provider_used": getattr(llm_client, "provider", "zai"),
                    "fallback_used": False,
                },
            )
            metrics["model"] = os.getenv("ZAI_VISION_MODEL", "glm-4.5v")
            _mark_execution_mode(metrics, "llm")
    except Exception as exc:
        payload = fallback_payload
        payload["fallback_reason"] = str(exc)[:160]
        if metrics is not None:
            _mark_execution_mode(metrics, "fallback")
            metrics["provider_used"] = getattr(llm_client, "provider", "zai")
            metrics["model"] = os.getenv("ZAI_VISION_MODEL", "glm-4.5v")
            metrics["fallback_used"] = True
            metrics["fallback_reason"] = type(exc).__name__

    return _validated(ImageAnalysisResult, payload, "Vision inspection agent returned invalid data.")


async def reasoning_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    intake: IntakeResult,
    context: ContextResult,
    image_analysis: ImageAnalysisResult | None = None,
    metrics: dict | None = None,
) -> ReasoningResult:
    if not use_llm_agents():
        _mark_execution_mode(metrics, "fallback")
        return _validated(
            ReasoningResult,
            fallback_reasoning(complaint_text, intake, context, image_analysis),
            "Fallback reasoning returned invalid data.",
        )

    prompt = (
        f"Complaint:\n{complaint_text}\n\n"
        f"Intake:\n{intake.model_dump_json(indent=2)}\n\n"
        f"Context:\n{context.model_dump_json(indent=2)}\n\n"
        f"Visual evidence:\n{image_analysis.model_dump_json(indent=2) if image_analysis else 'null'}"
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
        payload = fallback_reasoning(complaint_text, intake, context, image_analysis)
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
            "ASK_CLARIFICATION": "CLARIFY",
            "NEEDS_CLARIFICATION": "CLARIFY",
            "REQUEST_CLARIFICATION": "CLARIFY",
            "REFUND_REQUEST": "REFUND",
        }
        payload["decision"] = decision_aliases.get(payload["decision"], payload["decision"])
        if payload["decision"] not in {"REFUND", "RESHIP", "CLARIFY", "ESCALATE", "DISMISS"}:
            _mark_execution_mode(metrics, "fallback")
            payload = fallback_reasoning(complaint_text, intake, context, image_analysis)
    try:
        payload["confidence"] = max(0.0, min(1.0, float(payload.get("confidence", 0))))
    except (TypeError, ValueError):
        raise RuntimeError("Reasoning agent returned invalid confidence.")
    payload["requires_human_review"] = bool(payload.get("requires_human_review"))
    payload["clarification_needed"] = bool(payload.get("clarification_needed"))
    if payload.get("clarification_message") is not None:
        payload["clarification_message"] = str(payload.get("clarification_message")).strip() or None
    if payload["decision"] == "CLARIFY":
        payload["clarification_needed"] = True
        payload["requires_human_review"] = True
        if not payload.get("clarification_message"):
            payload["clarification_message"] = _clarification_message()
    if payload["clarification_needed"]:
        payload["decision"] = "CLARIFY"
        payload["requires_human_review"] = True
        if not payload.get("clarification_message"):
            payload["clarification_message"] = _clarification_message()
    if _should_auto_reship_wrong_item(intake, context):
        payload["decision"] = "RESHIP"
        payload["requires_human_review"] = False
        payload["clarification_needed"] = False
        payload["clarification_message"] = None
        payload["confidence"] = max(payload["confidence"], 0.82)
        if not payload.get("rationale") or "manual" in str(payload.get("rationale")).lower():
            payload["rationale"] = (
                "Wrong item reported for an order found in the system; replacement is the preferred policy path."
            )
    if _should_dismiss_refund_request(complaint_text, intake, context):
        payload["decision"] = "DISMISS"
        payload["requires_human_review"] = False
        payload["clarification_needed"] = False
        payload["clarification_message"] = None
        payload["confidence"] = max(payload["confidence"], 0.9)
        payload["rationale"] = (
            "Change-of-mind refund request is outside the seller refund window and no damage or fulfillment issue is claimed."
        )
    if _missing_claim_contradiction(complaint_text, intake, image_analysis):
        payload["decision"] = "CLARIFY"
        payload["requires_human_review"] = True
        payload["clarification_needed"] = True
        payload["clarification_message"] = _missing_package_clarification_message()
        payload["confidence"] = min(max(payload["confidence"], 0.78), 0.86)
        payload["rationale"] = (
            "Contradiction detected: the complaint says the order is missing, but uploaded visual evidence "
            "shows a package or item was received. Customer clarification is needed before refund or reship."
        )
    if image_analysis and image_analysis.image_provided and image_analysis.image_analyzed:
        if (
            image_analysis.damage_detected is True
            and image_analysis.matches_order_item is not False
            and context.order_found
            and image_analysis.confidence >= 0.75
            and not payload.get("clarification_needed")
        ):
            payload["requires_human_review"] = False
            payload["confidence"] = max(payload["confidence"], min(0.96, image_analysis.confidence))
            if intake.issue_type == "damaged_item" and payload["decision"] == "ESCALATE":
                payload["decision"] = "REFUND"
            if payload["decision"] not in {"REFUND", "RESHIP"} and intake.issue_type == "damaged_item":
                payload["decision"] = "REFUND"
            evidence = image_analysis.evidence.strip()
            if evidence and "visual" not in str(payload.get("rationale", "")).lower():
                payload["rationale"] = f"{payload.get('rationale', '').strip()} Visual evidence supports damage: {evidence}".strip()
        elif image_analysis.damage_detected is False and intake.issue_type == "damaged_item":
            payload["decision"] = "CLARIFY"
            payload["requires_human_review"] = True
            payload["clarification_needed"] = True
            payload["clarification_message"] = _evidence_mismatch_clarification_message()
            payload["confidence"] = min(payload["confidence"], 0.74)
            payload["rationale"] = (
                "The complaint reports damage, but uploaded visual evidence does not show clear damage. "
                "Seller review and customer clarification are needed before refund or reship."
            )
        if image_analysis.human_review_required:
            payload["requires_human_review"] = True
    if isinstance(payload.get("rationale"), str):
        payload["rationale"] = payload["rationale"].strip()
    if _contains_malay_markers(payload.get("rationale")) or _contains_malay_markers(payload.get("clarification_message")):
        _mark_execution_mode(metrics, "fallback")
        payload = fallback_reasoning(complaint_text, intake, context, image_analysis)
    try:
        return _validated(ReasoningResult, payload, "Reasoning agent returned invalid data.")
    except RuntimeError:
        _mark_execution_mode(metrics, "fallback")
        return _validated(
            ReasoningResult,
            fallback_reasoning(complaint_text, intake, context, image_analysis),
            "Fallback reasoning returned invalid data.",
        )


async def response_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    reasoning: ReasoningResult,
    context: ContextResult,
    metrics: dict | None = None,
) -> ResponseResult:
    if reasoning.clarification_needed:
        _mark_execution_mode(metrics, "fallback")
        return _validated(
            ResponseResult,
            fallback_response(reasoning, context),
            "Clarification response returned invalid data.",
        )

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
    payload = _sanitize_response_customer_names(payload, context)
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
    if _contains_malay_markers(payload["supervisor_note"]):
        payload["supervisor_note"] = _english_supervisor_note(ReasoningResult(**reasoning.model_dump()), context)
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
    image_analysis: ImageAnalysisResult | None = None,
) -> dict:
    if _missing_claim_contradiction(complaint_text, intake, image_analysis):
        return {
            "decision": "CLARIFY",
            "confidence": 0.82,
            "rationale": (
                "Contradiction detected: customer says the order is missing, but uploaded visual evidence shows "
                "a package or item was received. Clarification is required before refund or reship."
            ),
            "requires_human_review": True,
            "clarification_needed": True,
            "clarification_message": _missing_package_clarification_message(),
        }
    if (
        image_analysis
        and image_analysis.image_analyzed
        and image_analysis.damage_detected is False
        and intake.issue_type == "damaged_item"
    ):
        return {
            "decision": "CLARIFY",
            "confidence": 0.72,
            "rationale": "Complaint reports damage but uploaded image does not show clear damage; seller review and customer clarification are needed.",
            "requires_human_review": True,
            "clarification_needed": True,
            "clarification_message": _evidence_mismatch_clarification_message(),
        }
    if not context.order_found:
        return {
            "decision": "ESCALATE",
            "confidence": 0.9,
            "rationale": "Order context is missing, so a support agent should verify the customer and order details.",
            "requires_human_review": True,
            "clarification_needed": False,
            "clarification_message": None,
        }
    if intake.issue_type == "damaged_item":
        confidence = 0.9
        rationale = "The customer reports a damaged item for an order that exists in the system."
        if image_analysis and image_analysis.image_analyzed and image_analysis.damage_detected is True:
            confidence = max(confidence, min(0.96, image_analysis.confidence))
            rationale = f"{rationale} Uploaded visual evidence also supports visible damage."
        return {
            "decision": "REFUND",
            "confidence": confidence,
            "rationale": rationale,
            "requires_human_review": False,
            "clarification_needed": False,
            "clarification_message": None,
        }
    if intake.issue_type in {"wrong_item", "delivery_delay"}:
        return {
            "decision": "RESHIP",
            "confidence": 0.82,
            "rationale": "The issue can likely be resolved by arranging a replacement or delivery follow-up.",
            "requires_human_review": False,
            "clarification_needed": False,
            "clarification_message": None,
        }
    if _should_dismiss_refund_request(complaint_text, intake, context):
        return {
            "decision": "DISMISS",
            "confidence": 0.9,
            "rationale": "The customer is requesting a change-of-mind refund outside the seller refund window, with no damage or fulfillment issue claimed.",
            "requires_human_review": False,
            "clarification_needed": False,
            "clarification_message": None,
        }
    return {
        "decision": "ESCALATE",
        "confidence": 0.65,
        "rationale": "The complaint is not specific enough for an automated decision.",
        "requires_human_review": True,
        "clarification_needed": False,
        "clarification_message": None,
    }


def fallback_response(reasoning: ReasoningResult, context: ContextResult) -> dict:
    order = context.order_data or {}
    name = _context_customer_name(context) or "there"
    item = order.get("item") or "your item"
    amount = ""
    if order.get("total") and order.get("currency"):
        amount = f" {order['currency']} {float(order['total']):.2f}"

    if reasoning.clarification_needed:
        message = _customer_safe_clarification_message(reasoning.clarification_message, name)
        english = (
            f"Hi {name}, thanks for sharing the details. "
            "We need one quick clarification before the seller can review the correct next step. "
            f"{message} Once confirmed, we will review the correct next step."
        )
        bahasa = (
            f"Hai {name}, terima kasih kerana berkongsi maklumat ini. "
            "Kami perlukan satu pengesahan ringkas sebelum penjual boleh menyemak tindakan seterusnya. "
            "Sila sahkan isu tersebut dan, jika ada, muat naik gambar yang jelas untuk barang atau bungkusan yang rosak. "
            "Selepas disahkan, kami akan semak tindakan seterusnya."
        )
    elif reasoning.decision == "REFUND":
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
        "supervisor_note": _english_supervisor_note(reasoning, context),
    }


def fallback_image_analysis(image_provided: bool) -> dict:
    return {
        "image_provided": image_provided,
        "image_analyzed": False,
        "item_visible": None,
        "package_visible": None,
        "damage_detected": None,
        "damage_level": "unknown",
        "damage_type": None,
        "matches_order_item": None,
        "matched_order_item": None,
        "confidence": 0,
        "evidence": "Image could not be analyzed. Decision should rely on complaint text and order context.",
        "human_review_required": True,
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
