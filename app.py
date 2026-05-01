"""Vercel ASGI entrypoint.

The FastAPI application lives in backend.main; this shim lets platforms that
scan the repository root discover the existing `app` object.
"""

from backend.main import app

