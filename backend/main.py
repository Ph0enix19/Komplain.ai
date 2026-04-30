from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.agents import (
    build_event,
    context_agent,
    intake_agent,
    reasoning_agent,
    response_agent,
    supervisor_logic,
)
from backend.llm import ILMUClient
from backend.models import (
    ComplaintCreate,
    ContextResult,
    IntakeResult,
    ReasoningResult,
    ResponseResult,
    TestLLMRequest,
    TestLLMResponse,
)
from backend.storage import DataManager

load_dotenv(override=True)

app = FastAPI(title="Komplain.ai Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_manager = DataManager(data_dir="data")
ilmu_client = ILMUClient()


async def run_intake_agent(complaint_text: str) -> dict:
    return (await intake_agent(ilmu_client, complaint_text)).model_dump()


async def run_context_agent(intake: dict) -> dict:
    return (await context_agent(ilmu_client, data_manager, IntakeResult(**intake))).model_dump()


async def run_reasoning_agent(complaint_text: str, intake: dict, context: dict) -> dict:
    return (
        await reasoning_agent(
            ilmu_client,
            complaint_text,
            IntakeResult(**intake),
            ContextResult(**context),
        )
    ).model_dump()


async def run_response_agent(complaint_text: str, reasoning: dict, context: dict) -> dict:
    return (
        await response_agent(
            ilmu_client,
            complaint_text,
            ReasoningResult(**reasoning),
            ContextResult(**context),
        )
    ).model_dump()


async def run_supervisor_logic(reasoning: dict, context: dict) -> dict:
    return await supervisor_logic(
        ilmu_client,
        ReasoningResult(**reasoning),
        ContextResult(**context),
    )


async def run_complaint_pipeline(complaint_id: str, complaint_text: str, created_at: str) -> dict:
    intake_payload = await run_intake_agent(complaint_text)
    intake = IntakeResult(**intake_payload)
    data_manager.add_event(build_event(complaint_id, "intake", "Intake completed", intake_payload))

    context_payload = await run_context_agent(intake_payload)
    context = ContextResult(**context_payload)
    data_manager.add_event(build_event(complaint_id, "context", "Context loaded", context_payload))

    reasoning_payload = await run_reasoning_agent(complaint_text, intake_payload, context_payload)
    reasoning = ReasoningResult(**reasoning_payload)
    data_manager.add_event(build_event(complaint_id, "reasoning", "Reasoning completed", reasoning_payload))

    response_payload, supervisor = await asyncio.gather(
        run_response_agent(complaint_text, reasoning_payload, context_payload),
        run_supervisor_logic(reasoning_payload, context_payload),
    )
    response = ResponseResult(**response_payload)
    data_manager.add_event(build_event(complaint_id, "response", "Response generated", response_payload))
    data_manager.add_event(build_event(complaint_id, "supervisor", "Supervisor decision", supervisor))

    complaint = {
        "id": complaint_id,
        "complaint_text": complaint_text,
        "created_at": created_at,
        "status": "COMPLETED",
        "intake": intake.model_dump(),
        "context": context.model_dump(),
        "reasoning": reasoning.model_dump(),
        "response": response.model_dump(),
        "supervisor": supervisor,
    }
    data_manager.add_complaint(complaint)
    return complaint


async def _run_pipeline_in_background(complaint_id: str, complaint_text: str, created_at: str) -> None:
    try:
        await run_complaint_pipeline(complaint_id, complaint_text, created_at)
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


@app.on_event("startup")
def startup() -> None:
    data_manager.load_all()


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "complaints_count": len(data_manager.complaints),
    }


@app.post("/api/test-llm", response_model=TestLLMResponse)
async def test_llm(req: TestLLMRequest) -> TestLLMResponse:
    try:
        output = await ilmu_client.chat(req.prompt, system="You are Komplain.ai assistant.")
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

    return TestLLMResponse(model=ilmu_client.model, output=output)


@app.post("/api/complaints")
async def create_complaint(payload: ComplaintCreate) -> dict:
    complaint_id = str(uuid4())
    complaint_text = payload.complaint_text.strip()
    if payload.order_id and payload.order_id not in complaint_text:
        complaint_text = f"{complaint_text}\n\nOrder ID: {payload.order_id}"
    created_at = datetime.now(timezone.utc).isoformat()

    placeholder = {
        "id": complaint_id,
        "complaint_text": complaint_text,
        "created_at": created_at,
        "status": "PROCESSING",
    }
    data_manager.add_complaint(placeholder)

    asyncio.create_task(_run_pipeline_in_background(complaint_id, complaint_text, created_at))

    return placeholder


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
                yield f"data: {event}\n\n"
                sent += 1

            if sent >= 5:
                break

            retries += 1
            await asyncio.sleep(0.5)

        yield "event: done\n"
        yield 'data: {"status": "complete"}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")
