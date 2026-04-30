from __future__ import annotations

import os

import pytest

from backend.llm import ILMUClient


@pytest.mark.requires_llm
@pytest.mark.asyncio
async def test_llm_provider_swap(monkeypatch: pytest.MonkeyPatch) -> None:
    providers = [
        ("groq", "GROQ_API_KEY"),
        ("ilmu", "ILMU_API_KEY"),
    ]
    configured_providers = [
        (provider, api_key_env_var) for provider, api_key_env_var in providers if os.getenv(api_key_env_var)
    ]

    if not configured_providers:
        pytest.skip("Set GROQ_API_KEY or ILMU_API_KEY to run LLM provider smoke tests.")

    for provider, _api_key_env_var in configured_providers:
        monkeypatch.setenv("LLM_PROVIDER", provider)
        client = ILMUClient()
        response = await client.chat_json(
            'Return exactly {"status": "ok"}.',
            "You are a strict JSON API. Return only a JSON object.",
            max_tokens=512,
        )

        assert isinstance(response, dict)
        assert "status" in response
