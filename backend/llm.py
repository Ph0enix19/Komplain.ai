from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx


class ILMUClient:
    MAX_TOKENS = 512

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("ILMU_BASE_URL", "https://api.ilmu.ai/v1")).rstrip("/")
        self.model = model or os.getenv("ILMU_MODEL", "ilmu-glm-5.1")
        self.api_key = os.getenv("ILMU_API_KEY")
        self.timeout = timeout or float(os.getenv("ILMU_TIMEOUT", "180"))
        self.reasoning_effort = os.getenv("ILMU_REASONING_EFFORT", "low")

    async def chat(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("ILMU_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens or self.MAX_TOKENS,
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        data = await self._create_chat_completion(payload)

        try:
            message = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected response format from ILMU API.") from exc

        if isinstance(message, str):
            return message
        if isinstance(message, list):
            text_parts = []
            for item in message:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(str(item.get("text", "")))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "".join(text_parts)

        raise RuntimeError("Unexpected message content from ILMU API.")

    async def chat_json(
        self,
        prompt: str,
        system: str,
        *,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("ILMU_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens or self.MAX_TOKENS,
            "response_format": {"type": "json_object"},
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort

        data = await self._create_chat_completion(payload)
        try:
            raw_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected response format from ILMU API.") from exc
        if not isinstance(raw_text, str):
            raise RuntimeError("ILMU API returned no JSON message content.")
        return self._extract_json_object(raw_text)

    async def _create_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._chat_completions_url()
        headers = {
            "Authorization": f"Bearer {self.api_key or ''}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return data

    def _chat_completions_url(self) -> str:
        root = self.base_url.rstrip("/")
        if root.endswith("/chat/completions"):
            return root
        return f"{root}/chat/completions"

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            raise RuntimeError("ILMU API returned an empty response.")

        candidates = [stripped]

        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
        if fenced_match:
            candidates.insert(0, fenced_match.group(1))

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidates.append(stripped[start : end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        raise RuntimeError("ILMU API did not return valid JSON.")
