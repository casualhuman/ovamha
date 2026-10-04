"""Confirmation gate: nothing unconfirmed counts.

Every value (AI-extracted, safety-net flag, or keypad entry) is held as a
proposal. Only an explicit confirm event moves it into the confirmed record,
and only the confirmed record is passed to rules, handover, FHIR and SMS.
Anything left unconfirmed is discarded when the encounter is finalised.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .extract import NOT_CAPTURED, Extraction
from .safety_net import LABELS, Flag

# Numbers default to keypad entry (decision 3); voice is for symptoms and history.
KEYPAD_FIELDS = {
    "gestational_age_weeks": "Gestational age (weeks)",
    "systolic": "Systolic BP (mmHg)",
    "diastolic": "Diastolic BP (mmHg)",
    "systolic_repeat": "Repeat systolic BP (mmHg)",
    "diastolic_repeat": "Repeat diastolic BP (mmHg)",
    "pulse": "Pulse (/min)",
    "temperature": "Temperature (°C)",
    "fetal_heart_rate": "Fetal heart rate (/min)",
}
OTHER_LABELS = {
    "previous_pregnancies": "Previous pregnancies",
    "births": "Babies born alive",
    "bleeding_amount": "Bleeding amount",
    "urine_protein": "Urine protein",
    "severe_pe_symptoms": "Symptoms of severe pre-eclampsia",
}


def label(f: str) -> str:
    return KEYPAD_FIELDS.get(f) or LABELS.get(f) or OTHER_LABELS.get(f) or f.replace("_", " ").capitalize()


@dataclass
class Proposal:
    field: str
    value: object
    source: str  # "voice-ai-extracted" | "ai-safety-net" | "keypad"
    evidence: str = ""


@dataclass
class ConfirmEvent:
    field: str
    proposed: object
    confirmed: object
    source: str
    at: str


@dataclass
class Session:
    worker_id: str = "chw-demo-01"
    proposals: dict[str, Proposal] = field(default_factory=dict)
    confirmed: dict[str, object] = field(default_factory=dict)
    events: list[ConfirmEvent] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)

    # ---- proposals ----
    def propose_from_extraction(self, ex: Extraction) -> None:
        for f, fv in ex.fields.items():
            if f == "gestational_age_weeks":
                continue  # number: keypad (a voiced GA is shown as a hint only)
            if fv.value != NOT_CAPTURED:
                self.proposals[f] = Proposal(f, fv.value, "voice-ai-extracted", fv.evidence)

    def propose_flags(self, flags: list[Flag]) -> None:
        for fl in flags:
            if fl.field not in self.proposals:
                self.proposals[fl.field] = Proposal(fl.field, True, "ai-safety-net", f"{fl.evidence} ({fl.reason})")

    def propose_keypad(self, f: str, value) -> None:
        self.proposals[f] = Proposal(f, value, "keypad")

    # ---- worker actions ----
    def confirm(self, f: str, value=None) -> None:
        """Worker confirms a proposal, optionally correcting its value."""
        p = self.proposals[f]
        final = p.value if value is None else value
        self.confirmed[f] = final
        self.sources[f] = p.source if value is None or value == p.value else f"{p.source}+worker-corrected"
        self.events.append(ConfirmEvent(f, p.value, final, p.source, datetime.now(timezone.utc).isoformat()))

    def reject(self, f: str) -> None:
        self.proposals.pop(f, None)
        self.confirmed.pop(f, None)
        self.sources.pop(f, None)

    # ---- read-back ----
    def readback(self) -> list[tuple[str, str, str, str]]:
        """(field, label, value text, source) for every pending proposal."""
        return [(f, label(f), fmt(p.value), p.source) for f, p in self.proposals.items() if f not in self.confirmed]

    def finalise(self) -> dict:
        """Discard everything unconfirmed and return the confirmed record."""
        self.proposals = {f: p for f, p in self.proposals.items() if f in self.confirmed}
        return dict(self.confirmed)


def fmt(v) -> str:
    if v is True:
        return "Yes"
    if v is False:
        return "No"
    return str(v)
