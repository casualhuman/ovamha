"""AI safety net: scan the whole transcript for danger-sign terms that extraction
did not capture as a current, positive field (for example, mentioned in passing
or in the past), and return them as flags for the worker to confirm.

Add-only: a flag can raise a question; it can never clear a field, delay a rule
prompt or override a rule. Unconfirmed flags are discarded by confirm.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from .extract import Extraction, find_mentions
from .lexicon import FIELD_TERMS, SAFETY_NET_ONLY

LABELS = {
    "vaginal_bleeding": "Vaginal bleeding",
    "dizziness": "Dizziness",
    "fainting": "Fainting",
    "headache": "Headache",
    "visual_disturbance": "Visual disturbance",
    "convulsions": "Convulsions",
    "fever": "Fever",
    "abdominal_pain": "Abdominal pain",
    "breathing_difficulty": "Difficulty breathing",
    "unconscious": "Unconscious / not responding",
    "vomiting": "Vomiting",
    "reduced_fetal_movement": "Reduced fetal movement",
    "waters_broken": "Waters broken",
    "swelling": "Swelling",
    "foul_discharge": "Foul-smelling vaginal discharge",
}


@dataclass
class Flag:
    field: str
    label: str
    evidence: str
    reason: str
    source: str = "ai-safety-net"  # or "ai-classifier" (detect.py, mode "both")


def scan(ex: Extraction) -> list[Flag]:
    table = {**FIELD_TERMS, **SAFETY_NET_ONLY}
    flags: dict[str, Flag] = {}
    for m in find_mentions(ex.transcript, ex.lang, table):
        if m.negated:
            continue  # "no fever": nothing to raise
        fv = ex.fields.get(m.field)
        if fv is not None and fv.value is True:
            continue  # already captured as a current positive field
        if m.field in flags:
            continue
        reason = "mentioned in the past or as resolved" if m.past else "mentioned but not captured as a field"
        flags[m.field] = Flag(m.field, LABELS.get(m.field, m.field), m.clause, reason)
    return list(flags.values())
