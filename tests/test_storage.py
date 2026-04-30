from __future__ import annotations

from backend.storage import DataManager


def test_add_complaint_enforces_five_record_fifo_cap(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()

    for index in range(6):
        manager.add_complaint({"id": f"complaint-{index}", "complaint_text": f"Complaint {index}"})

    assert [complaint["id"] for complaint in manager.complaints] == [
        "complaint-1",
        "complaint-2",
        "complaint-3",
        "complaint-4",
        "complaint-5",
    ]


def test_get_order_returns_none_for_missing_id(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()

    assert manager.get_order("missing-order") is None


def test_agent_events_are_pruned_when_associated_complaint_is_evicted(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()

    for index in range(5):
        manager.add_complaint({"id": f"complaint-{index}", "complaint_text": f"Complaint {index}"})
    manager.add_event({"id": "event-old", "complaint_id": "complaint-0", "step": "intake", "message": "old"})
    manager.add_event({"id": "event-kept", "complaint_id": "complaint-4", "step": "intake", "message": "kept"})

    manager.add_complaint({"id": "complaint-5", "complaint_text": "Complaint 5"})

    assert [event["id"] for event in manager.agent_events] == ["event-kept"]
