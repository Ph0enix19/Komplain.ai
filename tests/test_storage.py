from __future__ import annotations

from backend.storage import DataManager


def test_complaint_save_and_load_works(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()
    manager.add_complaint({"id": "complaint-1", "complaint_text": "Damaged item"})

    reloaded = DataManager(data_dir=str(tmp_path))
    reloaded.load_all()

    assert reloaded.get_complaint("complaint-1") == {
        "id": "complaint-1",
        "complaint_text": "Damaged item",
    }


def test_order_defaults_and_lookup_work(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()

    assert manager.orders == []
    assert manager.get_order("missing") is None

    manager.orders = [{"order_id": "KM-1001", "customer_name": "Aisyah"}]

    assert manager.get_order("KM-1001") == {"order_id": "KM-1001", "customer_name": "Aisyah"}


def test_fifo_queue_keeps_only_last_five_complaints(tmp_path) -> None:
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


def test_add_complaint_replaces_existing_id_without_growing_queue(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()

    manager.add_complaint({"id": "complaint-1", "complaint_text": "Original"})
    manager.add_complaint({"id": "complaint-1", "complaint_text": "Updated"})

    assert len(manager.complaints) == 1
    assert manager.get_complaint("complaint-1")["complaint_text"] == "Updated"


def test_agent_events_are_pruned_when_complaint_is_evicted(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()

    for index in range(5):
        manager.add_complaint({"id": f"complaint-{index}", "complaint_text": f"Complaint {index}"})
    manager.add_event({"id": "event-old", "complaint_id": "complaint-0", "step": "intake", "message": "old"})
    manager.add_event({"id": "event-kept", "complaint_id": "complaint-4", "step": "intake", "message": "kept"})

    manager.add_complaint({"id": "complaint-5", "complaint_text": "Complaint 5"})

    assert [event["id"] for event in manager.agent_events] == ["event-kept"]


def test_agent_event_save_and_load_works(tmp_path) -> None:
    manager = DataManager(data_dir=str(tmp_path))
    manager.load_all()
    manager.add_complaint({"id": "complaint-1", "complaint_text": "Damaged item"})
    manager.add_event({"id": "event-1", "complaint_id": "complaint-1", "step": "intake", "message": "done"})

    reloaded = DataManager(data_dir=str(tmp_path))
    reloaded.load_all()

    assert reloaded.agent_events == [
        {"id": "event-1", "complaint_id": "complaint-1", "step": "intake", "message": "done"}
    ]
