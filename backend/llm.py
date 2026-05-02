from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any

import httpx

_REASONING_DEFAULT = object()
DEFAULT_ZAI_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
DEFAULT_ZAI_MODEL = "glm-5.1"
COST_PER_1K_TOKENS_RM = 0.002
logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    # Lightweight fallback when providers omit token usage details.
    return int(len(text.split()) * 1.3)


class ILMUClient:
    MAX_TOKENS = 512
    MAX_NULL_CONTENT_RETRIES = 2
    PROVIDERS = {"groq", "ilmu", "zai"}
    FALLBACK_PROVIDER = "groq"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        provider: str | None = None,
        enable_fallback: bool = True,
    ) -> None:
        self.provider = (provider or os.getenv("LLM_PROVIDER", "zai")).strip().lower()
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
            timeout_env_var = "GROQ_TIMEOUT"
            timeout_default = os.getenv("ILMU_TIMEOUT", "180")
        elif self.provider == "zai":
            self.base_url = (base_url or os.getenv("ZAI_BASE_URL", DEFAULT_ZAI_BASE_URL)).rstrip("/")
            self.model = model or os.getenv("ZAI_MODEL", DEFAULT_ZAI_MODEL)
            self.api_key = os.getenv("ZAI_API_KEY")
            self.api_key_env_var = "ZAI_API_KEY"
            self.reasoning_effort = None
            self.supports_reasoning_effort = False
            self.thinking_type = os.getenv("ZAI_THINKING_TYPE", "disabled").strip().lower()
            self.temperature = float(os.getenv("ZAI_TEMPERATURE", "0.1"))
            timeout_env_var = "ZAI_TIMEOUT"
            timeout_default = "60"
        else:
            self.base_url = (base_url or os.getenv("ILMU_BASE_URL", "https://api.ilmu.ai/v1")).rstrip("/")
            self.model = model or os.getenv("ILMU_MODEL", "ilmu-glm")
            self.api_key = os.getenv("ILMU_API_KEY")
            self.api_key_env_var = "ILMU_API_KEY"
            self.reasoning_effort = os.getenv("ILMU_REASONING_EFFORT", "low")
            self.supports_reasoning_effort = True
            timeout_env_var = "ILMU_TIMEOUT"
            timeout_default = "180"

        self.timeout = timeout or float(os.getenv(timeout_env_var, timeout_default))
        self.fallback_client = (
            ILMUClient(provider=self.FALLBACK_PROVIDER, enable_fallback=False)
            if enable_fallback and self.provider == "zai"
            else None
        )
        self.last_provider_metadata: dict[str, Any] = {
            "provider_used": self.provider,
            "fallback_used": False,
        }

    async def chat(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> str:
        return await self._run_with_fallback(
            lambda client: client._chat_once(
                prompt,
                system=system,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )
        )

    async def _chat_once(
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
        self._apply_provider_options(payload)
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

    async def chat_with_usage(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> tuple[str, dict[str, Any]]:
        message, usage = await self._run_with_fallback(
            lambda client: client._chat_with_usage_once(
                prompt,
                system=system,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )
        )
        return message, self._usage_with_provider_metadata(usage)

    async def _chat_with_usage_once(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> tuple[str, dict[str, int]]:
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
        self._apply_provider_options(payload)
        message, usage = await self._create_message_with_retries(payload, include_usage=True)

        if isinstance(message, str):
            return message, usage
        if isinstance(message, list):
            text_parts = []
            for item in message:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(str(item.get("text", "")))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "".join(text_parts), usage

        raise RuntimeError(f"Unexpected message content from {self.provider.upper()} API.")

    async def chat_json(
        self,
        prompt: str,
        system: str,
        *,
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> dict[str, Any]:
        return await self._run_with_fallback(
            lambda client: client._chat_json_once(
                prompt,
                system,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )
        )

    async def _chat_json_once(
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
        self._apply_provider_options(payload)

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

    def _apply_provider_options(self, payload: dict[str, Any]) -> None:
        if self.provider != "zai":
            return
        payload["temperature"] = self.temperature
        if self.thinking_type in {"", "none", "default"}:
            return
        payload["thinking"] = {"type": self.thinking_type}

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
        include_usage: bool = False,
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

        last_usage = {"input_tokens": self._estimate_payload_input_tokens(payload), "output_tokens": 0}
        for variant in variants:
            for attempt in range(self.MAX_NULL_CONTENT_RETRIES + 1):
                try:
                    data = await self._create_chat_completion(variant)
                except httpx.HTTPStatusError as exc:
                    if self._should_retry_without_response_format(exc, variant, expected_json=expected_json):
                        break
                    raise
                message = self._message_content(data)
                last_usage = self._usage_from_response(data, variant, message)
                if isinstance(message, (str, list)):
                    if include_usage:
                        return message, last_usage
                    return message
                if attempt < self.MAX_NULL_CONTENT_RETRIES:
                    await asyncio.sleep(0.75 * (attempt + 1))
        if include_usage:
            return None, last_usage
        return None

    def _should_retry_without_response_format(
        self,
        exc: httpx.HTTPStatusError,
        payload: dict[str, Any],
        *,
        expected_json: bool,
    ) -> bool:
        return bool(
            expected_json
            and self.provider == "zai"
            and "response_format" in payload
            and exc.response.status_code in {400, 404, 422, 429}
        )

    @staticmethod
    def _message_content(data: dict[str, Any]) -> Any:
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected response format from LLM provider.") from exc
        return message.get("content")

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            raise RuntimeError("LLM provider returned an empty response.")

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

        raise RuntimeError("LLM provider did not return valid JSON.")

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
        return await self._chat_once(
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

    async def chat_json_with_usage(
        self,
        prompt: str,
        system: str,
        *,
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        payload, usage = await self._run_with_fallback(
            lambda client: client._chat_json_with_usage_once(
                prompt,
                system,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )
        )
        return payload, self._usage_with_provider_metadata(usage)

    async def _chat_json_with_usage_once(
        self,
        prompt: str,
        system: str,
        *,
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> tuple[dict[str, Any], dict[str, int]]:
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
        self._apply_provider_options(payload)

        raw_text, usage = await self._create_message_with_retries(payload, expected_json=True, include_usage=True)
        if not isinstance(raw_text, str):
            raw_text, fallback_usage = await self._chat_key_value_with_usage(
                prompt, system, max_tokens=max_tokens, reasoning_effort=reasoning_effort
            )
            usage = self._merge_usage(usage, fallback_usage)
        return self._extract_structured_object(raw_text), usage

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

    async def _chat_key_value_with_usage(
        self,
        prompt: str,
        system: str,
        *,
        max_tokens: int | None = None,
        reasoning_effort: Any = _REASONING_DEFAULT,
    ) -> tuple[str, dict[str, int]]:
        safe_system = re.sub(r"\bJSON\b", "plain text", system, flags=re.IGNORECASE)
        safe_prompt = re.sub(r"\bJSON\b", "plain text fields", prompt, flags=re.IGNORECASE)
        key_value_system = (
            f"{safe_system}\n\n"
            "Return the requested fields as plain text. "
            "Use exactly one field per line in this format: key: value. "
            "Do not use markdown, bullets, tables, or explanations."
        )
        return await self._chat_with_usage_once(
            safe_prompt,
            system=key_value_system,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )

    @classmethod
    def _usage_from_response(
        cls,
        data: dict[str, Any],
        payload: dict[str, Any],
        message: Any,
    ) -> dict[str, int]:
        usage = data.get("usage") if isinstance(data, dict) else None
        usage = usage if isinstance(usage, dict) else {}

        input_tokens = cls._coerce_token_count(usage.get("prompt_tokens") or usage.get("input_tokens"))
        output_tokens = cls._coerce_token_count(usage.get("completion_tokens") or usage.get("output_tokens"))
        total_tokens = cls._coerce_token_count(usage.get("total_tokens"))

        estimated_input = cls._estimate_payload_input_tokens(payload)
        if input_tokens is None:
            input_tokens = estimated_input
        if output_tokens is None:
            if total_tokens is not None and total_tokens >= input_tokens:
                output_tokens = total_tokens - input_tokens
            else:
                output_tokens = estimate_tokens(cls._message_text(message))

        return {"input_tokens": input_tokens, "output_tokens": output_tokens}

    @staticmethod
    def _coerce_token_count(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _estimate_payload_input_tokens(cls, payload: dict[str, Any]) -> int:
        messages = payload.get("messages", [])
        parts = []
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, dict):
                    parts.append(cls._message_text(message.get("content", "")))
        return estimate_tokens("\n".join(parts))

    @staticmethod
    def _message_text(message: Any) -> str:
        if isinstance(message, str):
            return message
        if isinstance(message, list):
            text_parts = []
            for item in message:
                if isinstance(item, dict):
                    text_parts.append(str(item.get("text") or item.get("content") or ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "".join(text_parts)
        if message is None:
            return ""
        return json.dumps(message, ensure_ascii=False)

    @staticmethod
    def _merge_usage(*usages: dict[str, int]) -> dict[str, int]:
        return {
            "input_tokens": sum(int(usage.get("input_tokens", 0)) for usage in usages),
            "output_tokens": sum(int(usage.get("output_tokens", 0)) for usage in usages),
        }

    async def _run_with_fallback(self, operation):
        try:
            result = await operation(self)
        except Exception as exc:
            if not self.fallback_client:
                self._set_provider_metadata(self.provider, fallback_used=False, fallback_reason=self._fallback_reason(exc))
                raise

            fallback_reason = self._fallback_reason(exc)
            logger.warning(
                "LLM provider %s failed; falling back to %s. reason=%s",
                self.provider,
                self.FALLBACK_PROVIDER,
                fallback_reason,
            )
            try:
                result = await operation(self.fallback_client)
            except Exception as fallback_exc:
                self._set_provider_metadata(
                    self.FALLBACK_PROVIDER,
                    fallback_used=True,
                    fallback_reason=fallback_reason,
                )
                raise RuntimeError(
                    f"Primary LLM provider {self.provider} failed and "
                    f"{self.FALLBACK_PROVIDER} fallback also failed: {self._fallback_reason(fallback_exc)}"
                ) from fallback_exc

            self._set_provider_metadata(
                self.FALLBACK_PROVIDER,
                fallback_used=True,
                fallback_reason=fallback_reason,
            )
            return result

        self._set_provider_metadata(self.provider, fallback_used=False)
        return result

    def _set_provider_metadata(
        self,
        provider_used: str,
        *,
        fallback_used: bool,
        fallback_reason: str | None = None,
    ) -> None:
        self.last_provider_metadata = {
            "provider_used": provider_used,
            "fallback_used": fallback_used,
        }
        if fallback_reason:
            self.last_provider_metadata["fallback_reason"] = fallback_reason

    def _usage_with_provider_metadata(self, usage: dict[str, int]) -> dict[str, Any]:
        enriched: dict[str, Any] = dict(usage)
        enriched.update(self.last_provider_metadata)
        return enriched

    @staticmethod
    def _fallback_reason(exc: Exception) -> str:
        if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
            return "timeout"
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
            if status_code == 429:
                return "rate_limit"
            return f"http_{status_code}"
        if isinstance(exc, httpx.HTTPError):
            return "provider_error"

        message = str(exc).lower()
        if "not configured" in message:
            return "missing_key"
        if any(marker in message for marker in ("unexpected", "empty response", "valid json", "invalid")):
            return "invalid_response"
        return "provider_error"
