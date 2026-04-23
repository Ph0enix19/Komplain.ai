from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

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
from backend.llm import OllamaClient
from backend.models import ComplaintCreate, TestLLMRequest, TestLLMResponse
from backend.storage import DataManager

app = FastAPI(title="Komplain.ai Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_manager = DataManager(data_dir="data")
ollama_client = OllamaClient()


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
    output = await ollama_client.chat(req.prompt, system="You are Komplain.ai assistant.")
    return TestLLMResponse(model=ollama_client.model, output=output)


@app.post("/api/complaints")
def create_complaint(payload: ComplaintCreate) -> dict:
    complaint_id = str(uuid4())
    complaint_text = payload.complaint_text.strip()
    if payload.order_id and payload.order_id not in complaint_text:
        complaint_text = f"{complaint_text}\n\nOrder ID: {payload.order_id}"

    intake = intake_agent(complaint_text)
    data_manager.add_event(build_event(complaint_id, "intake", "Intake completed", intake.model_dump()))

    context = context_agent(data_manager, intake)
    data_manager.add_event(build_event(complaint_id, "context", "Context loaded", context.model_dump()))

    reasoning = reasoning_agent(intake, context)
    data_manager.add_event(
        build_event(complaint_id, "reasoning", "Reasoning completed", reasoning.model_dump())
    )

    response = response_agent(reasoning, context)
    data_manager.add_event(
        build_event(complaint_id, "response", "Response generated", response.model_dump())
    )

    supervisor = supervisor_logic(reasoning)
    data_manager.add_event(
        build_event(complaint_id, "supervisor", "Supervisor decision", supervisor)
    )

    complaint = {
        "id": complaint_id,
        "complaint_text": complaint_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETED",
        "intake": intake.model_dump(),
        "context": context.model_dump(),
        "reasoning": reasoning.model_dump(),
        "response": response.model_dump(),
        "supervisor": supervisor,
    }
    data_manager.add_complaint(complaint)
    return complaint


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
        yield "data: {\"status\": \"complete\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
