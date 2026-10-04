"""A finalised encounter: confirmed data + rule results + identifiers. Built only from confirmed data."""
from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .rules import RuleResult

# Short codes avoid look-alike characters (0/O, 1/I/L) so they survive SMS and reading aloud.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def short_code(n: int = 4) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(n))


@dataclass
class Encounter:
    confirmed: dict
    sources: dict  # field -> provenance source ("voice-ai-extracted", "ai-safety-net", "keypad", ...)
    results: list[RuleResult]
    lang: str
    worker_id: str
    asr_model: str
    woman_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    card_code: str = field(default_factory=lambda: short_code(6))
    encounter_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    code: str = field(default_factory=short_code)  # encounter code carried by SMS
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    facility: str = "Demo Community Health Post"
    facility_id: str = "demo-chp"
    referral_facility: str = "Demo District Hospital"
    referral_facility_id: str = "demo-district-hospital"
    worker_role: str = "Community health worker"
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # the pregnancy (EpisodeOfCare)
    national_id: dict | None = None  # consented ID check: {"document": ..., "method": "document-shown", "verified": False, "consent_at": ...}
    sms: dict | None = None  # {"text", "sent", "channel"} once the referral SMS is sent
    referral_status: str = "requested"  # requested -> accepted (ACK) | rejected (FULL)

    @property
    def referral(self) -> bool:
        return any(r.fired for r in self.results)

    @property
    def fired(self) -> list[RuleResult]:
        return [r for r in self.results if r.fired]
