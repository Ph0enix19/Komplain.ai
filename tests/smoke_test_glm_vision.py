from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.llm import DEFAULT_ZAI_VISION_BASE_URL, DEFAULT_ZAI_VISION_MODEL, ILMUClient


DAMAGE_SYSTEM = """You are a visual quality inspection agent for e-commerce complaints.
Inspect the customer image and decide whether the packaging or item is visibly damaged.
Return only valid JSON with exactly these keys:
- damage_detected: boolean
- damage_level: one of "none", "minor", "major", "unclear"
- visible_item_or_packaging: short string
- confidence: number between 0 and 1
- evidence: short string
Do not include markdown or explanations outside JSON."""


async def inspect_image(client: ILMUClient, image: str) -> dict:
    prompt = (
        "Classify this customer evidence image for an e-commerce complaint. "
        "Focus on visible physical damage, torn packaging, crushed boxes, cracks, dents, stains, or broken items."
    )
    return await client.chat_json_with_image(
        image,
        prompt,
        DAMAGE_SYSTEM,
        max_tokens=512,
        thinking_type=os.getenv("ZAI_VISION_THINKING_TYPE", "disabled"),
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test Z.ai / GLM vision damage inspection.")
    parser.add_argument("images", nargs="+", help="Image file paths or publicly reachable image URLs.")
    args = parser.parse_args()

    load_dotenv(override=True)
    client = ILMUClient(enable_fallback=False)

    print("Komplain.ai GLM vision smoke test")
    print(f"Base URL: {os.getenv('ZAI_VISION_BASE_URL', DEFAULT_ZAI_VISION_BASE_URL)}")
    print(f"Model: {os.getenv('ZAI_VISION_MODEL', DEFAULT_ZAI_VISION_MODEL)}")
    print(f"API key configured: {'yes' if os.getenv(client.api_key_env_var) else 'no'}")
    print()

    exit_code = 0
    for image in args.images:
        label = image if image.startswith(("http://", "https://", "data:")) else str(Path(image))
        start = time.perf_counter()
        try:
            payload = await inspect_image(client, image)
        except httpx.HTTPStatusError as exc:
            elapsed = time.perf_counter() - start
            print(f"{label}: FAIL ({elapsed:.1f}s)")
            print(f"HTTP {exc.response.status_code}: {exc.response.text[:1000]}")
            exit_code = 1
            continue
        except Exception as exc:
            elapsed = time.perf_counter() - start
            print(f"{label}: FAIL ({elapsed:.1f}s)")
            print(f"{type(exc).__name__}: {exc}")
            exit_code = 1
            continue

        elapsed = time.perf_counter() - start
        print(f"{label}: PASS ({elapsed:.1f}s)")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
