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
    worker_name: str = ""  # display name, e.g. "Nurse Fati"
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # the pregnancy (EpisodeOfCare)
    national_id: dict | None = None  # consented ID check: {"document": ..., "method": "document-shown", "verified": False, "consent_at": ...}
    birth_date: str | None = None  # "YYYY-MM-DD", or "YYYY" when estimated
    birth_date_estimated: bool = False
    details: dict = field(default_factory=dict)  # ANC.A4 registration details
    profile: dict = field(default_factory=dict)  # ANC.B6 first-contact profile (empty if not collected)
    profile_derived: dict = field(default_factory=dict)  # GA weeks / EDD from LMP
    facility_level: str = "CHP"  # MCHP | CHP | CHC | BEmONC | CEmONC
    advice: list = field(default_factory=list)  # guideline.Advice items shown to the worker
    suggestion: str = "none"  # strongest suggestion: urgent_referral | refer_cemonc | refer_assessment | plan_cemonc_delivery | none
    next_contact: dict = field(default_factory=dict)
    decision: dict | None = None  # the WORKER's decision: {"choice": "urgent"|"planned"|"none", "reason", "at"}
    referral_steps: dict = field(default_factory=dict)  # consent, checklist done, call/ambulance times
    sms: dict | None = None  # {"text", "sent", "channel"} once the referral SMS is sent
    referral_status: str = "requested"  # requested -> accepted (ACK) | rejected (FULL)

    @property
    def referral(self) -> bool:
        """True only when the health worker decided to refer (and, for urgent referral, she consented)."""
        if not self.decision:
            return False
        if self.decision["choice"] == "urgent":
            return bool(self.referral_steps.get("consent"))
        return self.decision["choice"] == "planned"

    @property
    def urgent(self) -> bool:
        return bool(self.decision and self.decision["choice"] == "urgent" and self.referral)

    @property
    def fired(self) -> list[RuleResult]:
        return [r for r in self.results if r.fired]
