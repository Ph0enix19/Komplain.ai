from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.storage import DataManager


def test_health_returns_status_and_counts(tmp_path, monkeypatch) -> None:
    test_manager = DataManager(data_dir=str(tmp_path))
    monkeypatch.setattr("backend.main.data_manager", test_manager)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "time" in payload
    assert payload["complaints_count"] == 0
