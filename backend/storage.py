from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DataManager:
    """Simple in-memory + JSON file storage for hackathon MVP."""

    MAX_COMPLAINTS = 5

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.complaints_path = self.data_dir / "complaints.json"
        self.orders_path = self.data_dir / "orders.json"
        self.agent_events_path = self.data_dir / "agent_events.json"

        self.complaints: list[dict[str, Any]] = []
        self.orders: list[dict[str, Any]] = []
        self.agent_events: list[dict[str, Any]] = []

    def load_all(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.complaints = self._load_json(self.complaints_path, default=[])
        self.orders = self._load_json(self.orders_path, default=[])
        self.agent_events = self._load_json(self.agent_events_path, default=[])

    def save_complaints(self) -> None:
        self._save_json(self.complaints_path, self.complaints)

    def save_agent_events(self) -> None:
        self._save_json(self.agent_events_path, self.agent_events)

    def add_complaint(self, complaint: dict[str, Any]) -> None:
        complaint_id = complaint.get("id")
        self.complaints = [c for c in self.complaints if c.get("id") != complaint_id]
        self.complaints.append(complaint)
        self.complaints = self.complaints[-self.MAX_COMPLAINTS :]
        active_ids = {c["id"] for c in self.complaints}
        self.agent_events = [
            event for event in self.agent_events if event["complaint_id"] in active_ids
        ]
        self.save_complaints()
        self.save_agent_events()

    def add_event(self, event: dict[str, Any]) -> None:
        self.agent_events.append(event)
        self.save_agent_events()

    def get_complaint(self, complaint_id: str) -> dict[str, Any] | None:
        return next((c for c in self.complaints if c["id"] == complaint_id), None)

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        return next((o for o in self.orders if o.get("order_id") == order_id), None)

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            with path.open("w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)
            return default

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _save_json(path: Path, payload: Any) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
