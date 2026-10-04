"""Device outbox and automatic sync to the hub FHIR server (spec 3.2 steps 4-5, section 10).

Nobody presses "send": a finished encounter's transaction Bundle is written to the
outbox on this device (SY-01) and a background worker uploads it whenever the hub is
reachable, retrying with backoff on interrupted connections (SY-05). Uploads are
idempotent because every resource is a conditional create (SY-02). Referral status
changes (ACK/FULL) are queued the same way and applied with If-Match on the Task
version (SY-03).

Outbox: OVAMHA_DATA/outbox/*.json (default ~/.ovamha/outbox), never in the repo, encrypted at rest (secure_store).
"""
from __future__ import annotations

import os
import threading
import time
import urllib.error
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import audit, fhir_client, secure_store

_lock = threading.Lock()
_state = {"last_attempt": None, "last_success": None, "last_error": None, "hub": fhir_client.FHIR_BASE}


def _dir(name: str) -> Path:
    d = Path(os.environ.get("OVAMHA_DATA", Path.home() / ".ovamha")) / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def enqueue_bundle(code: str, bundle: dict) -> None:
    _write({"kind": "bundle", "code": code, "bundle": bundle})


def enqueue_task_status(code: str, status: str) -> None:
    _write({"kind": "task-status", "code": code, "status": status})


def _write(item: dict) -> None:
    item |= {"queued_at": _now(), "attempts": 0}
    name = f"{time.time_ns()}-{uuid.uuid4().hex[:6]}.json"
    with _lock:
        secure_store.write_json(_dir("outbox") / name, item)


def pending() -> list[dict]:
    return [secure_store.read_json(p) | {"file": p.name} for p in sorted(_dir("outbox").glob("*.json"))]


def status(code: str | None = None) -> dict:
    items = pending()
    mine = [i for i in items if code is None or i["code"] == code]
    synced = code is not None and (_dir("sent") / f"{code}.json").exists()
    return {**_state, "pending": len(items), "pending_for_encounter": len(mine), "synced": synced}


def _task_for(code: str) -> str | None:
    found = fhir_client.get(f"Task?identifier=https://fhir.ovamha.org/id/referral-task|{code}")
    for e in found.get("entry", []):
        return f"Task/{e['resource']['id']}"
    return None


def _apply(item: dict) -> None:
    if item["kind"] == "bundle":
        resp = fhir_client.post_transaction(item["bundle"])
        secure_store.write_json(_dir("sent") / f"{item['code']}.json", {"at": _now(), "ids": fhir_client.server_ids(resp)})
    elif item["kind"] == "task-status":
        task = _task_for(item["code"])
        if task is None:
            raise RuntimeError("referral Task not on the hub yet")
        fhir_client.set_task_status(task, item["status"])


def flush() -> int:
    """Upload everything in the outbox, in order. Returns how many items were sent."""
    sent = 0
    with _lock:
        files = sorted(_dir("outbox").glob("*.json"))
    _state["last_attempt"] = _now()
    if not files:
        return 0
    if not fhir_client.available():
        _state["last_error"] = f"Hub not reachable at {fhir_client.FHIR_BASE}"
        return 0
    for p in files:
        item = secure_store.read_json(p)
        try:
            _apply(item)
        except (urllib.error.URLError, OSError, RuntimeError, ValueError) as exc:
            item["attempts"] += 1
            item["last_error"] = str(exc)
            secure_store.write_json(p, item)
            audit.log("fhir-upload-failed", outcome="failure", encounter=item["code"], kind=item["kind"])
            _state["last_error"] = str(exc)
            break  # keep order: a status change must not overtake its Bundle
        p.unlink()
        audit.log("fhir-upload", encounter=item["code"], kind=item["kind"])  # SY-07
        sent += 1
    if sent:
        _state["last_success"], _state["last_error"] = _now(), None
    return sent


def start_worker(interval: float = 15.0) -> None:
    """Background sync: try now, then every `interval` seconds, backing off to 5 minutes on failure."""
    def loop() -> None:
        wait = interval
        while True:
            try:
                flush()
                wait = interval if _state["last_error"] is None else min(wait * 2, 300)
            except Exception as exc:  # never let the worker die
                _state["last_error"] = str(exc)
                wait = min(wait * 2, 300)
            time.sleep(wait)

    threading.Thread(target=loop, name="ovamha-sync", daemon=True).start()
