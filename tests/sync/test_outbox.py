"""Outbox + automatic sync (SY-01, SY-02, SY-05), against a stand-in hub."""
import pytest

from ovamha_proto import fhir_client, sync


class FakeHub:
    def __init__(self):
        self.up = False
        self.bundles = []
        self.tasks = {}

    def available(self):
        return self.up

    def post_transaction(self, bundle):
        self.bundles.append(bundle)
        self.tasks["Task/1"] = "requested"
        return {"entry": [{"response": {"location": "Task/1/_history/1"}}]}

    def get(self, path):
        return {"entry": [{"resource": {"id": "1"}}]} if "Task?" in path and self.tasks else {}

    def set_task_status(self, ref, status):
        self.tasks[ref] = status
        return {"status": status}


@pytest.fixture
def hub(tmp_path, monkeypatch):
    monkeypatch.setenv("OVAMHA_DATA", str(tmp_path))
    h = FakeHub()
    for name in ("available", "post_transaction", "get", "set_task_status"):
        monkeypatch.setattr(fhir_client, name, getattr(h, name))
    sync._state["last_error"] = None
    return h


def test_offline_keeps_record_on_device(hub):
    sync.enqueue_bundle("ABCD", {"resourceType": "Bundle"})
    assert sync.flush() == 0
    st = sync.status("ABCD")
    assert st["pending_for_encounter"] == 1 and not st["synced"] and "not reachable" in st["last_error"]


def test_uploads_when_hub_comes_back(hub):
    sync.enqueue_bundle("ABCD", {"resourceType": "Bundle"})
    sync.flush()
    hub.up = True
    assert sync.flush() == 1
    st = sync.status("ABCD")
    assert st["synced"] and st["pending"] == 0 and len(hub.bundles) == 1


def test_ack_applies_after_bundle_in_order(hub):
    sync.enqueue_bundle("ABCD", {"resourceType": "Bundle"})
    sync.enqueue_task_status("ABCD", "accepted")
    hub.up = True
    assert sync.flush() == 2
    assert hub.tasks["Task/1"] == "accepted"


def test_status_change_waits_if_task_not_on_hub(hub):
    sync.enqueue_task_status("ZZZZ", "accepted")
    hub.up = True
    assert sync.flush() == 0
    assert sync.status()["pending"] == 1
