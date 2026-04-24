from __future__ import annotations

import asyncio
import os
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


def _validated(model_cls, payload: dict, error_message: str):
    try:
        return model_cls(**payload)
    except ValidationError as exc:
        raise RuntimeError(error_message) from exc


async def intake_agent(llm_client: ILMUClient, complaint_text: str) -> IntakeResult:
    payload = await asyncio.wait_for(
        llm_client.chat_json(
            prompt=f"Complaint:\n{complaint_text}",
            system=INTAKE_SYSTEM,
            max_tokens=1024,
        ),
        timeout=AGENT_LLM_TIMEOUT_SECONDS,
    )
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
    payload = await asyncio.wait_for(
        llm_client.chat_json(
            prompt=(
                f"Intake:\n{intake.model_dump_json(indent=2)}\n\n"
                f"Order lookup result:\n{order if order is not None else 'null'}"
            ),
            system=CONTEXT_SYSTEM,
            max_tokens=1024,
        ),
        timeout=AGENT_LLM_TIMEOUT_SECONDS,
    )
    payload["order_found"] = bool(order)
    payload["order_data"] = order
    return _validated(ContextResult, payload, "Context agent returned invalid data.")


async def reasoning_agent(
    llm_client: ILMUClient,
    complaint_text: str,
    intake: IntakeResult,
    context: ContextResult,
) -> ReasoningResult:
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
    payload = await asyncio.wait_for(
        llm_client.chat_json(
            prompt=(
                f"Complaint:\n{complaint_text}\n\n"
                f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\n"
                f"Context:\n{context.model_dump_json(indent=2)}"
            ),
            system=RESPONSE_SYSTEM,
            max_tokens=1536,
        ),
        timeout=AGENT_LLM_TIMEOUT_SECONDS,
    )
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
    payload = await asyncio.wait_for(
        llm_client.chat_json(
            prompt=(
                f"Reasoning:\n{reasoning.model_dump_json(indent=2)}\n\n"
                f"Context:\n{context.model_dump_json(indent=2)}"
            ),
            system=SUPERVISOR_SYSTEM,
            max_tokens=1024,
        ),
        timeout=AGENT_LLM_TIMEOUT_SECONDS,
    )
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
