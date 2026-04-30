from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

import httpx

_REASONING_DEFAULT = object()


class ILMUClient:
    MAX_TOKENS = 512
    MAX_NULL_CONTENT_RETRIES = 2
    PROVIDERS = {"groq", "ilmu"}

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
        if self.provider not in self.PROVIDERS:
            allowed = ", ".join(sorted(self.PROVIDERS))
            raise RuntimeError(f"Unsupported LLM_PROVIDER '{self.provider}'. Expected one of: {allowed}.")

        if self.provider == "groq":
            default_base_url = "https://api.groq.com/openai/v1"
            self.base_url = (base_url or os.getenv("GROQ_BASE_URL", default_base_url)).rstrip("/")
            self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            self.api_key = os.getenv("GROQ_API_KEY")
            self.api_key_env_var = "GROQ_API_KEY"
            self.reasoning_effort = None
            self.supports_reasoning_effort = False
        else:
            self.base_url = (base_url or os.getenv("ILMU_BASE_URL", "https://api.ilmu.ai/v1")).rstrip("/")
            self.model = model or os.getenv("ILMU_MODEL", "ilmu-glm-5.1")
            self.api_key = os.getenv("ILMU_API_KEY")
            self.api_key_env_var = "ILMU_API_KEY"
            self.reasoning_effort = os.getenv("ILMU_REASONING_EFFORT", "low")
            self.supports_reasoning_effort = True

        timeout_env_var = "GROQ_TIMEOUT" if self.provider == "groq" else "ILMU_TIMEOUT"
        self.timeout = timeout or float(os.getenv(timeout_env_var, os.getenv("ILMU_TIMEOUT", "180")))

    async def chat(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> str:
        if not self.api_key:
            raise RuntimeError(f"{self.api_key_env_var} is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens or self.MAX_TOKENS,
        }
        effort = self.reasoning_effort if reasoning_effort is _REASONING_DEFAULT else reasoning_effort
        if self.supports_reasoning_effort and effort:
            payload["reasoning_effort"] = effort
        message = await self._create_message_with_retries(payload)

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

        raise RuntimeError(f"Unexpected message content from {self.provider.upper()} API.")

    async def chat_json(
        self,
        prompt: str,
        system: str,
        *,
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError(f"{self.api_key_env_var} is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens or self.MAX_TOKENS,
            "response_format": {"type": "json_object"},
        }
        effort = self.reasoning_effort if reasoning_effort is _REASONING_DEFAULT else reasoning_effort
        if self.supports_reasoning_effort and effort:
            payload["reasoning_effort"] = effort

        raw_text = await self._create_message_with_retries(payload, expected_json=True)
        if not isinstance(raw_text, str):
            raw_text = await self._chat_key_value(
                prompt, system, max_tokens=max_tokens, reasoning_effort=reasoning_effort
            )
        return self._extract_structured_object(raw_text)

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

    async def _create_message_with_retries(
        self,
        payload: dict[str, Any],
        *,
        expected_json: bool = False,
    ) -> Any:
        variants = [dict(payload)]
        if expected_json:
            no_format = dict(payload)
            no_format.pop("response_format", None)
            variants.append(no_format)
        if "reasoning_effort" in payload:
            no_reasoning = dict(payload)
            no_reasoning.pop("reasoning_effort", None)
            variants.append(no_reasoning)

        for variant in variants:
            for attempt in range(self.MAX_NULL_CONTENT_RETRIES + 1):
                data = await self._create_chat_completion(variant)
                message = self._message_content(data)
                if isinstance(message, (str, list)):
                    return message
                if attempt < self.MAX_NULL_CONTENT_RETRIES:
                    await asyncio.sleep(0.75 * (attempt + 1))
        return None

    @staticmethod
    def _message_content(data: dict[str, Any]) -> Any:
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected response format from ILMU API.") from exc
        return message.get("content")

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

    async def _chat_key_value(
        self,
        prompt: str,
        system: str,
        *,
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> str:
        safe_system = re.sub(r"\bJSON\b", "plain text", system, flags=re.IGNORECASE)
        safe_prompt = re.sub(r"\bJSON\b", "plain text fields", prompt, flags=re.IGNORECASE)
        key_value_system = (
            f"{safe_system}\n\n"
            "Return the requested fields as plain text. "
            "Use exactly one field per line in this format: key: value. "
            "Do not use markdown, bullets, tables, or explanations."
        )
        return await self.chat(
            safe_prompt,
            system=key_value_system,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )

    @classmethod
    def _extract_structured_object(cls, text: str) -> dict[str, Any]:
        try:
            return cls._extract_json_object(text)
        except RuntimeError:
            parsed = cls._extract_key_value_object(text)
            if parsed:
                return parsed
            raise

    @staticmethod
    def _extract_key_value_object(text: str) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip().strip("-*")
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_").replace("-", "_")
            value = value.strip().strip('"').strip("'")
            if not key:
                continue
            lowered = value.lower()
            if lowered in {"true", "yes"}:
                parsed[key] = True
            elif lowered in {"false", "no"}:
                parsed[key] = False
            elif lowered in {"null", "none", "n/a"}:
                parsed[key] = None
            else:
                try:
                    parsed[key] = float(value) if "." in value else int(value)
                except ValueError:
                    parsed[key] = value
        return parsed
