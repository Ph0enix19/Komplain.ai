from __future__ import annotations

import asyncio
import time

from fastapi.testclient import TestClient

from backend import main
from backend.models import Decision
from backend.storage import DataManager


class FakeLLMClient:
    model = "fake-groq"
    provider = "groq"
    fallback_client = None

    async def chat(self, prompt: str, *_args, **_kwargs) -> str:
        return f"mocked response for: {prompt}"

    async def chat_with_usage(self, prompt: str, *_args, **_kwargs) -> tuple[str, dict]:
        return f"mocked response for: {prompt}", {
            "provider_used": self.provider,
            "fallback_used": False,
        }

    async def chat_json(self, _prompt: str, system: str, **_kwargs) -> dict:
        if "intake agent" in system:
            return {
                "customer_name": "Aisyah",
                "order_id": "KM-1001",
                "issue_type": "damaged_item",
                "sentiment": "negative",
                "language": "EN",
            }
        if "context agent" in system:
            return {"order_found": True, "notes": "Order found"}
        if "response agent" in system:
            return {
                "english": "We approved a refund.",
                "bahasa_malaysia": "Kami telah meluluskan bayaran balik.",
            }
        if "supervisor agent" in system:
            return {
                "requires_human_review": False,
                "priority": "normal",
                "supervisor_note": "No manual review needed.",
            }
        return {
            "decision": "REFUND",
            "confidence": 0.92,
            "rationale": "Delivered item arrived damaged.",
            "requires_human_review": False,
        }


def make_client(tmp_path, monkeypatch) -> TestClient:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()
    manager.orders = [
        {
            "order_id": "KM-1001",
            "customer_name": "Aisyah",
            "item": "Bluetooth Speaker",
            "status": "DELIVERED",
            "total": 129.0,
            "currency": "MYR",
        }
    ]
    monkeypatch.setattr(main, "data_manager", manager)
    monkeypatch.setattr(main, "ilmu_client", FakeLLMClient())
    monkeypatch.setenv("USE_LLM_AGENTS", "true")
    return TestClient(main.app)


def test_health_returns_200(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_response_contains_operational_fields(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        payload = client.get("/api/health").json()

    assert "time" in payload
    assert payload["complaints_count"] == 0


def test_test_llm_returns_valid_response(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post("/api/test-llm", json={"prompt": "hello"})

    assert response.status_code == 200
    assert response.json() == {
        "model": "fake-groq",
        "output": "mocked response for: hello",
        "provider_used": "groq",
        "fallback_used": False,
        "fallback_reason": None,
    }


def test_test_llm_rejects_empty_prompt(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post("/api/test-llm", json={"prompt": ""})

    assert response.status_code == 422


def test_create_complaint_returns_processing_placeholder(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post(
            "/api/complaints",
            json={"complaint_text": "My speaker arrived damaged", "order_id": "KM-1001"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PROCESSING"
    assert "id" in payload


def test_complaint_pipeline_produces_decision_confidence_and_bilingual_response(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post(
            "/api/complaints",
            json={"complaint_text": "My speaker arrived damaged", "order_id": "KM-1001"},
        )
        complaint_id = response.json()["id"]

        complaint = None
        for _ in range(20):
            get_response = client.get(f"/api/complaints/{complaint_id}")
            complaint = get_response.json()
            if complaint.get("status") == "COMPLETED":
                break
            time.sleep(0.05)

    assert complaint is not None
    assert complaint["reasoning"]["decision"] in {decision.value for decision in Decision}
    assert isinstance(complaint["reasoning"]["confidence"], float)
    assert complaint["response"]["english"]
    assert complaint["response"]["bahasa_malaysia"]


def test_get_missing_complaint_returns_404(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get("/api/complaints/missing")

    assert response.status_code == 404


def test_complaint_events_endpoint_returns_agent_steps(tmp_path, monkeypatch) -> None:
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post(
            "/api/complaints",
            json={"complaint_text": "My speaker arrived damaged", "order_id": "KM-1001"},
        )
        complaint_id = response.json()["id"]

        events = []
        for _ in range(20):
            events_response = client.get(f"/api/complaints/{complaint_id}/events")
            events = events_response.json()
            if len(events) >= 5:
                break
            time.sleep(0.05)

    assert {event["step"] for event in events} >= {"intake", "context", "reasoning", "response", "supervisor"}
    assert {event["execution_mode"] for event in events} == {"llm"}


def test_run_complaint_pipeline_directly_returns_completed_payload(tmp_path, monkeypatch) -> None:
    make_client(tmp_path, monkeypatch)

    result = asyncio.run(
        main.run_complaint_pipeline(
            complaint_id="complaint-1",
            complaint_text="My speaker arrived damaged\n\nOrder ID: KM-1001",
            created_at="2026-04-30T00:00:00+00:00",
        )
    )

    assert result["status"] == "COMPLETED"
    assert result["reasoning"]["decision"] == "REFUND"
    assert result["response"]["english"]
    assert result["response"]["bahasa_malaysia"]
    assert result["agent_metrics"]["intake"]["execution_mode"] == "llm"
