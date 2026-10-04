"""Minimal FHIR REST client for the local HAPI FHIR server (no internet needed).

FHIR_BASE defaults to http://localhost:8080/fhir (hub/docker-compose.yml).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

FHIR_BASE = os.environ.get("FHIR_BASE", "http://localhost:8080/fhir").rstrip("/")
HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}


def _req(method: str, path: str, body: dict | None = None, timeout: float = 15, headers: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{FHIR_BASE}/{path.lstrip('/')}", data=data, method=method, headers=HEADERS | (headers or {}))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def available() -> bool:
    try:
        _req("GET", "metadata", timeout=3)
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def post_transaction(bundle: dict) -> dict:
    """POST the transaction Bundle; returns the transaction-response Bundle."""
    return _req("POST", "", bundle)


def server_ids(response: dict) -> dict[str, str]:
    """resourceType -> 'Type/id' of the first created resource of each type."""
    out: dict[str, str] = {}
    for entry in response.get("entry", []):
        loc = entry.get("response", {}).get("location", "")
        if loc:
            ref = "/".join(loc.split("/")[:2])
            out.setdefault(ref.split("/")[0], ref)
    return out


def set_task_status(task_ref: str, status: str) -> dict:
    """Optimistic locking (SY-03): the PUT only applies to the version just read."""
    task = _req("GET", task_ref)
    task["status"] = status
    version = task.get("meta", {}).get("versionId")
    return _req("PUT", task_ref, task, headers={"If-Match": f'W/"{version}"'} if version else None)


def get(path: str) -> dict:
    return _req("GET", path)
