"""Referral SMS. Sends through a GSM modem with Gammu if configured, otherwise
writes to a SIMULATED outbox log (shown as simulated in the UI).

The SMS carries the encounter code only: never the woman's name or HIV status.
Replies: "ACK <code>" -> referral accepted; "FULL <code>" -> facility full (rejected).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .encounter import Encounter

from . import secure_store

OUTBOX = Path(os.environ.get("OVAMHA_OUTBOX", Path(__file__).resolve().parents[4] / "outbox"))
REFERRAL_NUMBER = os.environ.get("OVAMHA_REFERRAL_NUMBER", "+00000000000")


@dataclass
class Sms:
    direction: str  # "out" | "in"
    number: str
    text: str
    at: str
    channel: str  # "gsm-modem" | "SIMULATED"
    kind: str = "referral"  # "referral" | "reminder" | "reply"


def referral_text(e: Encounter) -> str:
    ga = e.confirmed.get("gestational_age_weeks")
    rules = ",".join(r.rule_id.replace("ANC.", "") for r in e.fired)
    parts = [f"OVAMHA REFERRAL {e.code}", "URGENT", f"{ga}wk" if isinstance(ga, (int, float)) else None, f"rule {rules}", f"from {e.facility}"]
    return " | ".join(p for p in parts if p) + f". Reply ACK {e.code} or FULL {e.code}"


def reminder_text(e: Encounter) -> str | None:
    """Appointment reminder to the woman (ARCH: date, facility and a danger-sign line only; no name, no diagnosis)."""
    date = e.next_contact.get("date") if e.next_contact else None
    if not date:
        return None
    from datetime import date as _d
    when = _d.fromisoformat(date).strftime("%d %b %Y")
    return (f"Ovamha reminder: your next antenatal visit is on {when} at {e.facility}. "
            "If you bleed, have a bad headache or blurred vision, fever, or the baby moves less, come to the clinic at once.")


def wants_reminder(e: Encounter) -> bool:
    return bool(e.details.get("phone")) and e.details.get("wants_reminders") == "yes"


def log(limit: int = 30) -> list[dict]:
    """Recent messages, newest last (for the demo phone)."""
    path = OUTBOX / "sms.jsonl"
    return secure_store.read_jsonl(path)[-limit:] if path.exists() else []


def _gammu_available() -> bool:
    return os.environ.get("OVAMHA_GSM") == "1" and shutil.which("gammu") is not None


def _log(sms: Sms) -> None:
    secure_store.append_jsonl(OUTBOX / "sms.jsonl", asdict(sms))  # phone numbers and text encrypted at rest (DB-02)


def send(text: str, number: str = REFERRAL_NUMBER, kind: str = "referral") -> Sms:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if _gammu_available():
        subprocess.run(["gammu", "sendsms", "TEXT", number, "-text", text], check=True, timeout=60)
        sms = Sms("out", number, text, now, "gsm-modem", kind)
    else:
        sms = Sms("out", number, text, now, "SIMULATED", kind)
    _log(sms)
    return sms


REPLY = re.compile(r"^\s*(ACK|FULL)\s+([A-Z0-9]{4})\s*$", re.I)
TASK_STATUS = {"ACK": "accepted", "FULL": "rejected"}


def handle_reply(text: str, e: Encounter, number: str = REFERRAL_NUMBER) -> str | None:
    """Apply an ACK/FULL reply to the encounter. Returns the new Task status, or None if not for this encounter."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _log(Sms("in", number, text, now, "gsm-modem" if _gammu_available() else "SIMULATED", "reply"))
    m = REPLY.match(text)
    if not m or m.group(2).upper() != e.code:
        return None
    e.referral_status = TASK_STATUS[m.group(1).upper()]
    return e.referral_status
