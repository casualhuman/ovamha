"""Audit trail (WHO ANC DAK ANC.NFXNREQ.016-021; architecture SEC-06, SY-07; MoHS HIS Policy 2021 s.3.9(a)-(b)).

Records who did what and when: sign-in and sign-out, failed and locked sign-ins, idle
sign-outs, opening or creating a woman's record, showing a woman her record, finishing
an encounter, SMS sent or received, FHIR exchange with the hub, and anonymised exports.

Entries hold identifiers only (worker ID, pseudonymous woman ID, encounter code), never
names, symptoms, transcripts or phone numbers, and are encrypted at rest (secure_store).
Production writes FHIR AuditEvent resources (IHE BALP) to the hub instead.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import secure_store

EVENTS = {
    "login", "login-failed", "login-locked", "logout", "idle-logout",
    "woman-created", "woman-opened", "record-shown-to-woman", "privacy-notice-given",
    "encounter-finished", "sms-sent", "sms-reminder-sent", "sms-received", "fhir-upload", "fhir-upload-failed", "export-anonymised",
}
FORBIDDEN_KEYS = {"name", "first_name", "family_name", "phone", "transcript", "text", "pin", "symptoms", "number"}


def _path():
    return secure_store.data_dir() / "audit.jsonl"


def log(event: str, worker_id: str | None = None, outcome: str = "success", **ids) -> None:
    if event not in EVENTS:
        raise ValueError(f"unknown audit event {event!r}")
    leaked = FORBIDDEN_KEYS & set(ids)
    if leaked:
        raise ValueError(f"audit entries must not hold personal details: {sorted(leaked)}")
    secure_store.append_jsonl(_path(), {
        "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "event": event, "worker_id": worker_id, "outcome": outcome, **ids,
    })


def read() -> list[dict]:
    return secure_store.read_jsonl(_path())
