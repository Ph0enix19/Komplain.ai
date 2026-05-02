from __future__ import annotations

import asyncio
import json
import re
import time
from email.parser import BytesParser
from email.policy import default
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from backend.agents import (
    build_event,
    context_agent,
    intake_agent,
    reasoning_agent,
    response_agent,
    supervisor_logic,
    vision_inspection_agent,
)
from backend.llm import COST_PER_1K_TOKENS_RM, ILMUClient
from backend.models import (
    ComplaintCreate,
    ContextResult,
    IntakeResult,
    ImageAnalysisResult,
    ReasoningResult,
    ResponseResult,
    TestLLMRequest,
    TestLLMResponse,
)
from backend.storage import DataManager

load_dotenv(override=True)

data_manager = DataManager(data_dir="data")
ilmu_client = ILMUClient()

UPLOAD_DIR = Path("data/uploads")
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    data_manager.load_all()
    yield


app = FastAPI(title="Komplain.ai Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def run_intake_agent(complaint_text: str, metrics: dict | None = None) -> dict:
    return (await intake_agent(ilmu_client, complaint_text, metrics=metrics)).model_dump()


async def run_context_agent(intake: dict, metrics: dict | None = None) -> dict:
    return (await context_agent(ilmu_client, data_manager, IntakeResult(**intake), metrics=metrics)).model_dump()


async def run_reasoning_agent(
    complaint_text: str,
    intake: dict,
    context: dict,
    image_analysis: dict | None = None,
    metrics: dict | None = None,
) -> dict:
    return (
        await reasoning_agent(
            ilmu_client,
            complaint_text,
            IntakeResult(**intake),
            ContextResult(**context),
            ImageAnalysisResult(**image_analysis) if image_analysis else None,
            metrics=metrics,
        )
    ).model_dump()


async def run_vision_inspection(
    complaint_text: str,
    context: dict,
    image_path: str | None,
    metrics: dict | None = None,
) -> dict:
    return (
        await vision_inspection_agent(
            ilmu_client,
            complaint_text,
            ContextResult(**context),
            image_path,
            metrics=metrics,
        )
    ).model_dump()


async def run_response_agent(
    complaint_text: str,
    reasoning: dict,
    context: dict,
    metrics: dict | None = None,
) -> dict:
    return (
        await response_agent(
            ilmu_client,
            complaint_text,
            ReasoningResult(**reasoning),
            ContextResult(**context),
            metrics=metrics,
        )
    ).model_dump()


async def run_supervisor_logic(reasoning: dict, context: dict, metrics: dict | None = None) -> dict:
    return await supervisor_logic(
        ilmu_client,
        ReasoningResult(**reasoning),
        ContextResult(**context),
        metrics=metrics,
    )


async def _run_timed_agent(agent: str, action) -> tuple[dict, dict]:
    metrics = {"agent": agent, "input_tokens": 0, "output_tokens": 0, "execution_mode": "unknown"}
    started_at = time.time()
    payload = await action(metrics)
    metrics["duration"] = round(time.time() - started_at, 2)
    return payload, metrics


def _payload_with_metrics(payload: dict, metrics: dict) -> dict:
    # Include agent telemetry in the event payload without changing existing fields.
    enriched = {
        **payload,
        "agent": metrics["agent"],
        "duration": metrics["duration"],
        "input_tokens": metrics["input_tokens"],
        "output_tokens": metrics["output_tokens"],
        "execution_mode": metrics["execution_mode"],
    }
    for key in ("provider_used", "fallback_used", "fallback_reason"):
        if key in metrics:
            enriched[key] = metrics[key]
    if "model" in metrics:
        enriched["model"] = metrics["model"]
    return enriched


def _pipeline_totals(metrics_list: list[dict]) -> dict:
    total_tokens = sum(item["input_tokens"] + item["output_tokens"] for item in metrics_list)
    return {
        "total_latency": round(sum(item["duration"] for item in metrics_list), 2),
        "total_tokens": total_tokens,
        "estimated_cost_rm": round((total_tokens / 1000) * COST_PER_1K_TOKENS_RM, 6),
    }


async def run_complaint_pipeline(
    complaint_id: str,
    complaint_text: str,
    created_at: str,
    image_path: str | None = None,
    image_url: str | None = None,
) -> dict:
    intake_payload, intake_metrics = await _run_timed_agent(
        "intake",
        lambda metrics: run_intake_agent(complaint_text, metrics),
    )
    intake = IntakeResult(**intake_payload)
    data_manager.add_event(
        build_event(
            complaint_id,
            "intake",
            "Intake completed",
            _payload_with_metrics(intake_payload, intake_metrics),
            intake_metrics,
        )
    )

    context_payload, context_metrics = await _run_timed_agent(
        "context",
        lambda metrics: run_context_agent(intake_payload, metrics),
    )
    context = ContextResult(**context_payload)
    data_manager.add_event(
        build_event(
            complaint_id,
            "context",
            "Context loaded",
            _payload_with_metrics(context_payload, context_metrics),
            context_metrics,
        )
    )

    image_analysis_payload = None
    vision_metrics = None
    if image_path:
        image_analysis_payload, vision_metrics = await _run_timed_agent(
            "vision",
            lambda metrics: run_vision_inspection(complaint_text, context_payload, image_path, metrics),
        )
        data_manager.add_event(
            build_event(
                complaint_id,
                "vision",
                "Visual evidence inspected",
                _payload_with_metrics(image_analysis_payload, vision_metrics),
                vision_metrics,
            )
        )

    reasoning_payload, reasoning_metrics = await _run_timed_agent(
        "reasoning",
        lambda metrics: run_reasoning_agent(
            complaint_text,
            intake_payload,
            context_payload,
            image_analysis_payload,
            metrics,
        ),
    )
    reasoning = ReasoningResult(**reasoning_payload)
    data_manager.add_event(
        build_event(
            complaint_id,
            "reasoning",
            "Reasoning completed",
            _payload_with_metrics(reasoning_payload, reasoning_metrics),
            reasoning_metrics,
        )
    )

    (response_payload, response_metrics), (supervisor, supervisor_metrics) = await asyncio.gather(
        _run_timed_agent(
            "response",
            lambda metrics: run_response_agent(complaint_text, reasoning_payload, context_payload, metrics),
        ),
        _run_timed_agent(
            "supervisor",
            lambda metrics: run_supervisor_logic(reasoning_payload, context_payload, metrics),
        ),
    )
    response = ResponseResult(**response_payload)
    data_manager.add_event(
        build_event(
            complaint_id,
            "response",
            "Response generated",
            _payload_with_metrics(response_payload, response_metrics),
            response_metrics,
        )
    )
    data_manager.add_event(
        build_event(
            complaint_id,
            "supervisor",
            "Supervisor decision",
            _payload_with_metrics(supervisor, supervisor_metrics),
            supervisor_metrics,
        )
    )

    agent_metrics = {
        item["agent"]: item
        for item in [
            intake_metrics,
            context_metrics,
            *([vision_metrics] if vision_metrics else []),
            reasoning_metrics,
            response_metrics,
            supervisor_metrics,
        ]
    }
    totals = _pipeline_totals(list(agent_metrics.values()))

    complaint = {
        "id": complaint_id,
        "complaint_text": complaint_text,
        "created_at": created_at,
        "status": "COMPLETED",
        "image_path": image_path,
        "image_url": image_url,
        "image_analysis": image_analysis_payload,
        "visual_evidence_used": bool(image_analysis_payload and image_analysis_payload.get("image_analyzed")),
        "intake": intake.model_dump(),
        "context": context.model_dump(),
        "reasoning": reasoning.model_dump(),
        "response": response.model_dump(),
        "supervisor": supervisor,
        "agent_metrics": agent_metrics,
        **totals,
    }
    data_manager.add_complaint(complaint)
    return complaint


async def _run_pipeline_in_background(
    complaint_id: str,
    complaint_text: str,
    created_at: str,
    image_path: str | None = None,
    image_url: str | None = None,
) -> None:
    try:
        await run_complaint_pipeline(complaint_id, complaint_text, created_at, image_path, image_url)
    except Exception as exc:
        data_manager.add_complaint(
            {
                "id": complaint_id,
                "complaint_text": complaint_text,
                "created_at": created_at,
                "status": "FAILED",
                "error": str(exc),
            }
        )


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "complaints_count": len(data_manager.complaints),
        "llm_provider": ilmu_client.provider,
        "llm_model": ilmu_client.model,
        "fallback_provider": ilmu_client.fallback_client.provider if ilmu_client.fallback_client else None,
    }


@app.post("/api/test-llm", response_model=TestLLMResponse)
async def test_llm(req: TestLLMRequest) -> TestLLMResponse:
    try:
        output, usage = await ilmu_client.chat_with_usage(req.prompt, system="You are Komplain.ai assistant.")
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="LLM provider request timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider returned HTTP {exc.response.status_code}.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Failed to reach LLM provider.") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="An agent request to the LLM provider timed out.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return TestLLMResponse(
        model=ilmu_client.model,
        output=output,
        provider_used=usage.get("provider_used"),
        fallback_used=bool(usage.get("fallback_used")),
        fallback_reason=usage.get("fallback_reason"),
    )


def _safe_upload_filename(original_name: str, complaint_id: str) -> str:
    suffix = Path(original_name or "").suffix.lower()
    stem = Path(original_name or "upload").stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")[:36] or "evidence"
    return f"{complaint_id}-{stem}{suffix}"


def _validate_image_upload(filename: str, content_type: str | None, content: bytes) -> None:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Image must be a jpg, jpeg, png, or webp file.")
    if content_type and content_type.lower() not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported image content type.")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded image must be 5MB or smaller.")


def _parse_multipart_body(content_type: str, body: bytes) -> tuple[dict[str, str], dict | None]:
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    fields: dict[str, str] = {}
    image: dict | None = None
    if not message.is_multipart():
        raise HTTPException(status_code=400, detail="Invalid multipart request.")
    for part in message.iter_parts():
        disposition = part.get("Content-Disposition", "")
        if "form-data" not in disposition:
            continue
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename:
            if name == "image":
                image = {
                    "filename": filename,
                    "content_type": part.get_content_type(),
                    "content": payload,
                }
        elif name:
            fields[str(name)] = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    return fields, image


async def _read_complaint_request(request: Request, complaint_id: str) -> tuple[ComplaintCreate, str | None, str | None]:
    content_type = request.headers.get("content-type", "")
    image_path = None
    image_url = None
    if content_type.lower().startswith("multipart/form-data"):
        fields, image = _parse_multipart_body(content_type, await request.body())
        payload = ComplaintCreate(
            complaint_text=(fields.get("complaint_text") or "").strip(),
            order_id=(fields.get("order_id") or None),
        )
        if image:
            _validate_image_upload(image["filename"], image["content_type"], image["content"])
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            filename = _safe_upload_filename(image["filename"], complaint_id)
            stored_path = UPLOAD_DIR / filename
            stored_path.write_bytes(image["content"])
            image_path = str(stored_path)
            image_url = f"/api/uploads/{filename}"
        return payload, image_path, image_url

    data = await request.json()
    return ComplaintCreate(**data), image_path, image_url


@app.post("/api/complaints")
async def create_complaint(request: Request) -> dict:
    complaint_id = str(uuid4())
    payload, image_path, image_url = await _read_complaint_request(request, complaint_id)
    complaint_text = payload.complaint_text.strip()
    if payload.order_id and payload.order_id not in complaint_text:
        complaint_text = f"{complaint_text}\n\nOrder ID: {payload.order_id}"
    created_at = datetime.now(timezone.utc).isoformat()

    placeholder = {
        "id": complaint_id,
        "complaint_text": complaint_text,
        "created_at": created_at,
        "status": "PROCESSING",
        "image_path": image_path,
        "image_url": image_url,
    }
    data_manager.add_complaint(placeholder)

    asyncio.create_task(_run_pipeline_in_background(complaint_id, complaint_text, created_at, image_path, image_url))

    return placeholder


@app.get("/api/uploads/{filename}")
def get_uploaded_image(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=404, detail="Image not found")
    path = UPLOAD_DIR / safe_name
    if not path.exists() or path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


@app.get("/api/complaints")
def list_complaints() -> list[dict]:
    return data_manager.complaints


@app.get("/api/complaints/{complaint_id}")
def get_complaint(complaint_id: str) -> dict:
    complaint = data_manager.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@app.get("/api/complaints/{complaint_id}/events")
def get_complaint_events(complaint_id: str) -> list[dict]:
    if not data_manager.get_complaint(complaint_id):
        raise HTTPException(status_code=404, detail="Complaint not found")
    return [e for e in data_manager.agent_events if e["complaint_id"] == complaint_id]


@app.get("/api/complaints/{complaint_id}/stream")
async def stream_complaint_events(complaint_id: str) -> StreamingResponse:
    if not data_manager.get_complaint(complaint_id):
        raise HTTPException(status_code=404, detail="Complaint not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        sent = 0
        retries = 0

        while retries < 30:
            matching = [e for e in data_manager.agent_events if e["complaint_id"] == complaint_id]
            while sent < len(matching):
                event = matching[sent]
                yield f"event: {event['step']}\n"
                yield f"data: {json.dumps(event)}\n\n"
                sent += 1

            current = data_manager.get_complaint(complaint_id)
            if sent >= 5 and current and current.get("status") != "PROCESSING":
                break

            retries += 1
            await asyncio.sleep(0.5)

        current = data_manager.get_complaint(complaint_id) or {}
        done_payload = {"status": "complete"}
        for key in ("total_latency", "total_tokens", "estimated_cost_rm"):
            if key in current:
                done_payload[key] = current[key]
        yield "event: done\n"
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
