"""Referral SMS. Sends through a GSM modem with Gammu if configured, otherwise
writes to a SIMULATED outbox log (shown as simulated in the UI).

The SMS carries the encounter code only: never the woman's name or HIV status.
Replies: "ACK <code>" -> referral accepted; "FULL <code>" -> facility full (rejected).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .encounter import Encounter

OUTBOX = Path(os.environ.get("OVAMHA_OUTBOX", Path(__file__).resolve().parents[4] / "outbox"))
REFERRAL_NUMBER = os.environ.get("OVAMHA_REFERRAL_NUMBER", "+00000000000")


@dataclass
class Sms:
    direction: str  # "out" | "in"
    number: str
    text: str
    at: str
    channel: str  # "gsm-modem" | "SIMULATED"


def referral_text(e: Encounter) -> str:
    ga = e.confirmed.get("gestational_age_weeks")
    rules = ",".join(r.rule_id.replace("ANC.", "") for r in e.fired)
    parts = [f"OVAMHA REFERRAL {e.code}", "URGENT", f"{ga}wk" if isinstance(ga, (int, float)) else None, f"rule {rules}", f"from {e.facility}"]
    return " | ".join(p for p in parts if p) + f". Reply ACK {e.code} or FULL {e.code}"


def _gammu_available() -> bool:
    return os.environ.get("OVAMHA_GSM") == "1" and shutil.which("gammu") is not None


def _log(sms: Sms) -> None:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    with open(OUTBOX / "sms.jsonl", "a") as fh:
        fh.write(json.dumps(asdict(sms)) + "\n")


def send(text: str, number: str = REFERRAL_NUMBER) -> Sms:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if _gammu_available():
        subprocess.run(["gammu", "sendsms", "TEXT", number, "-text", text], check=True, timeout=60)
        sms = Sms("out", number, text, now, "gsm-modem")
    else:
        sms = Sms("out", number, text, now, "SIMULATED")
    _log(sms)
    return sms


REPLY = re.compile(r"^\s*(ACK|FULL)\s+([A-Z0-9]{4})\s*$", re.I)
TASK_STATUS = {"ACK": "accepted", "FULL": "rejected"}


def handle_reply(text: str, e: Encounter, number: str = REFERRAL_NUMBER) -> str | None:
    """Apply an ACK/FULL reply to the encounter. Returns the new Task status, or None if not for this encounter."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _log(Sms("in", number, text, now, "gsm-modem" if _gammu_available() else "SIMULATED"))
    m = REPLY.match(text)
    if not m or m.group(2).upper() != e.code:
        return None
    e.referral_status = TASK_STATUS[m.group(1).upper()]
    return e.referral_status
