from __future__ import annotations

import httpx
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


def test_provider_switching_selects_zai_primary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "zai")
    monkeypatch.setenv("ZAI_API_KEY", "zai-key")
    monkeypatch.delenv("ZAI_BASE_URL", raising=False)
    monkeypatch.setenv("ZAI_MODEL", "glm-current-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")

    client = ILMUClient()

    assert client.provider == "zai"
    assert client.api_key_env_var == "ZAI_API_KEY"
    assert client.model == "glm-current-test"
    assert client.base_url == "https://api.z.ai/api/coding/paas/v4"
    assert client.fallback_client is not None
    assert client.fallback_client.provider == "groq"


def test_provider_switching_selects_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")

    client = ILMUClient()

    assert client.provider == "groq"
    assert client.api_key_env_var == "GROQ_API_KEY"
    assert client.fallback_client is None


def test_provider_switching_between_groq_zai_and_legacy_ilmu_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("ZAI_API_KEY", "zai-key")
    monkeypatch.setenv("ILMU_API_KEY", "ilmu-key")

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    groq_client = ILMUClient()
    assert groq_client.provider == "groq"
    assert groq_client.api_key_env_var == "GROQ_API_KEY"

    monkeypatch.setenv("LLM_PROVIDER", "zai")
    zai_client = ILMUClient()
    assert zai_client.provider == "zai"
    assert zai_client.api_key_env_var == "ZAI_API_KEY"

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


@pytest.mark.asyncio
async def test_missing_zai_key_falls_back_to_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "zai")
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
    client = ILMUClient()
    assert client.fallback_client is not None

    async def fake_groq_completion(payload: dict) -> dict:
        assert payload["model"] == "llama-3.1-8b-instant"
        return {
            "choices": [{"message": {"content": '{"status": "ok"}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
        }

    monkeypatch.setattr(client.fallback_client, "_create_chat_completion", fake_groq_completion)

    payload, usage = await client.chat_json_with_usage("Return status.", "Return JSON.")

    assert payload == {"status": "ok"}
    assert usage["input_tokens"] == 10
    assert usage["output_tokens"] == 3
    assert usage["provider_used"] == "groq"
    assert usage["fallback_used"] is True
    assert usage["fallback_reason"] == "missing_key"


@pytest.mark.asyncio
async def test_zai_api_failure_falls_back_to_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "zai")
    monkeypatch.setenv("ZAI_API_KEY", "zai-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    client = ILMUClient()
    assert client.fallback_client is not None

    request = httpx.Request("POST", f"{client.base_url}/chat/completions")
    response = httpx.Response(429, request=request)

    async def failing_zai_completion(_payload: dict) -> dict:
        raise httpx.HTTPStatusError("rate limited", request=request, response=response)

    async def fake_groq_completion(_payload: dict) -> dict:
        return {
            "choices": [{"message": {"content": '{"decision": "REFUND"}'}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
        }

    monkeypatch.setattr(client, "_create_chat_completion", failing_zai_completion)
    monkeypatch.setattr(client.fallback_client, "_create_chat_completion", fake_groq_completion)

    payload, usage = await client.chat_json_with_usage("Return decision.", "Return JSON.")

    assert payload == {"decision": "REFUND"}
    assert usage["provider_used"] == "groq"
    assert usage["fallback_used"] is True
    assert usage["fallback_reason"] == "rate_limit"


@pytest.mark.asyncio
async def test_zai_invalid_response_falls_back_to_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "zai")
    monkeypatch.setenv("ZAI_API_KEY", "zai-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    client = ILMUClient()
    assert client.fallback_client is not None

    async def malformed_zai_completion(_payload: dict) -> dict:
        return {
            "choices": [{"message": {"content": "not json"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        }

    async def fake_groq_completion(_payload: dict) -> dict:
        return {
            "choices": [{"message": {"content": '{"status": "recovered"}'}}],
            "usage": {"prompt_tokens": 9, "completion_tokens": 4, "total_tokens": 13},
        }

    monkeypatch.setattr(client, "_create_chat_completion", malformed_zai_completion)
    monkeypatch.setattr(client.fallback_client, "_create_chat_completion", fake_groq_completion)

    payload, usage = await client.chat_json_with_usage("Return status.", "Return JSON.")

    assert payload == {"status": "recovered"}
    assert usage["provider_used"] == "groq"
    assert usage["fallback_used"] is True
    assert usage["fallback_reason"] == "invalid_response"
