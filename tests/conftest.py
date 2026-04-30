from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--llm",
        action="store_true",
        default=False,
        help="run tests that call real LLM providers",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--llm"):
        return

    skip_llm = pytest.mark.skip(reason="requires --llm and provider API keys")
    for item in items:
        if "requires_llm" in item.keywords:
            item.add_marker(skip_llm)


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", request.node.name).strip("-")
    path = Path.cwd() / ".test-tmp" / f"{safe_name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path
