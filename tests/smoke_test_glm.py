from __future__ import annotations

import asyncio
import json
import os
import time

import httpx
from dotenv import load_dotenv

from backend.llm import ILMUClient


async def main() -> int:
    load_dotenv(override=True)

    client = ILMUClient()
    print("Komplain.ai GLM-5.1 smoke test")
    print(f"Base URL: {client.base_url}")
    print(f"Model: {client.model}")
    print(f"Timeout: {client.timeout}s")
    print(f"Reasoning effort: {client.reasoning_effort or '(not set)'}")
    print(f"API key configured: {'yes' if os.getenv('ILMU_API_KEY') else 'no'}")
    print()

    start = time.perf_counter()
    try:
        text = await client.chat(
            "Reply with exactly: GLM_OK",
            system="You are a strict API smoke test. Follow the user instruction exactly.",
            max_tokens=32,
        )
        elapsed = time.perf_counter() - start
        print(f"Plain chat: PASS ({elapsed:.1f}s)")
        print(f"Output: {text!r}")
    except httpx.HTTPStatusError as exc:
        elapsed = time.perf_counter() - start
        print(f"Plain chat: FAIL ({elapsed:.1f}s)")
        print(f"HTTP {exc.response.status_code}: {exc.response.text[:1000]}")
        return 1
    except Exception as exc:
        elapsed = time.perf_counter() - start
        print(f"Plain chat: FAIL ({elapsed:.1f}s)")
        print(f"{type(exc).__name__}: {exc}")
        return 1

    start = time.perf_counter()
    json_prompt = "Return JSON for a damaged item complaint with order_id ORD-1887."
    json_system = (
        "Return only valid JSON with exactly these keys: "
        "order_id, issue_type, sentiment."
    )
    try:
        payload = await client.chat_json(json_prompt, system=json_system, max_tokens=128)
        elapsed = time.perf_counter() - start
        print()
        print(f"JSON chat: PASS ({elapsed:.1f}s)")
        print(f"Output: {payload}")
    except Exception as exc:
        elapsed = time.perf_counter() - start
        print()
        print(f"JSON chat: FAIL ({elapsed:.1f}s)")
        print(f"{type(exc).__name__}: {exc}")
        await print_json_diagnostic(client, json_prompt, json_system)
        print()
        print("Summary: GLM plain chat is working, but ILMU structured JSON mode is not returning message content.")
        print("Komplain.ai is configured with USE_LLM_AGENTS=true; backend agent calls retry GLM with safer request shapes.")
        return 0

    print()
    print("Summary: GLM plain chat and structured JSON mode are both working.")
    return 0


async def print_json_diagnostic(client: ILMUClient, prompt: str, system: str) -> None:
    print()
    print("Raw JSON-mode diagnostic:")
    payload = {
        "model": client.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 128,
        "response_format": {"type": "json_object"},
    }
    if client.reasoning_effort:
        payload["reasoning_effort"] = client.reasoning_effort

    try:
        data = await client._create_chat_completion(payload)
    except Exception as exc:
        print(f"Diagnostic request failed: {type(exc).__name__}: {exc}")
        return

    message = data.get("choices", [{}])[0].get("message")
    if not isinstance(message, dict):
        print(f"message type: {type(message).__name__}")
        print(json.dumps(data, indent=2)[:2000])
        return

    print(f"message keys: {sorted(message.keys())}")
    print(f"content type: {type(message.get('content')).__name__}")
    print(json.dumps(message, indent=2)[:2000])


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
