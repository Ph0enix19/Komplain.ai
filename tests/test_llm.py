from __future__ import annotations

import pytest

from backend.llm import ILMUClient


@pytest.mark.asyncio
async def test_chat_json_returns_valid_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    client = ILMUClient()

    async def fake_completion(payload: dict) -> dict:
        assert payload["response_format"] == {"type": "json_object"}
        return {"choices": [{"message": {"content": '{"status": "ok"}'}}]}

    monkeypatch.setattr(client, "_create_chat_completion", fake_completion)

    assert await client.chat_json("Return status.", "Return JSON.") == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_json_extracts_json_from_markdown_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    client = ILMUClient()

    async def fake_completion(_payload: dict) -> dict:
        return {"choices": [{"message": {"content": '```json\n{"decision": "REFUND"}\n```'}}]}

    monkeypatch.setattr(client, "_create_chat_completion", fake_completion)

    assert await client.chat_json("Return decision.", "Return JSON.") == {"decision": "REFUND"}


@pytest.mark.asyncio
async def test_chat_json_falls_back_to_key_value_when_json_content_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    client = ILMUClient()

    async def fake_message(_payload: dict, *, expected_json: bool = False):
        assert expected_json is True
        return None

    async def fake_key_value(*_args, **_kwargs) -> str:
        return "status: ok\nconfidence: 0.82\nrequires_human_review: false"

    monkeypatch.setattr(client, "_create_message_with_retries", fake_message)
    monkeypatch.setattr(client, "_chat_key_value", fake_key_value)

    assert await client.chat_json("Return fields.", "Return JSON.") == {
        "status": "ok",
        "confidence": 0.82,
        "requires_human_review": False,
    }


def test_provider_switching_between_groq_and_ilmu_does_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("ILMU_API_KEY", "ilmu-key")

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    groq_client = ILMUClient()
    assert groq_client.provider == "groq"
    assert groq_client.api_key_env_var == "GROQ_API_KEY"

    monkeypatch.setenv("LLM_PROVIDER", "ilmu")
    ilmu_client = ILMUClient()
    assert ilmu_client.provider == "ilmu"
    assert ilmu_client.api_key_env_var == "ILMU_API_KEY"


def test_unsupported_provider_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    with pytest.raises(RuntimeError, match="Unsupported LLM_PROVIDER"):
        ILMUClient()


def test_extract_structured_object_parses_key_value_fallback() -> None:
    assert ILMUClient._extract_structured_object("decision: RESHIP\nconfidence: 1\nnote: replacement") == {
        "decision": "RESHIP",
        "confidence": 1,
        "note": "replacement",
    }
