"""Handover text: reported symptoms, measured observations and actions, kept separate.

Contains confirmed fields only (the Encounter is built from Session.finalise()).
"""
from __future__ import annotations

from .confirm import KEYPAD_FIELDS, fmt, label
from . import questionnaire
from .encounter import Encounter

SOURCE_TEXT = {
    "voice-ai-extracted": "reported (voice, confirmed)",
    "ai-safety-net": "raised by AI safety net, confirmed by worker",
    "keypad": "entered on keypad",
}


def _src(s: str) -> str:
    base = SOURCE_TEXT.get(s.split("+")[0], s)
    return base + ("; corrected by worker" if s.endswith("worker-corrected") else "")


def handover_text(e: Encounter) -> str:
    reported = [(f, v) for f, v in e.confirmed.items() if f not in KEYPAD_FIELDS]
    measured = [(f, v) for f, v in e.confirmed.items() if f in KEYPAD_FIELDS]
    lines = [
        f"OVAMHA HANDOVER  {e.code}  ({'URGENT REFERRAL' if e.referral else 'no referral rule fired'})",
        f"Card number: {e.card_code[:3]}-{e.card_code[3:]}   Time: {e.at}   From: {e.facility}   Worker: {e.worker_id}",
        "",
        "REPORTED SYMPTOMS (history)",
    ]
    lines += [f"  - {label(f)}: {fmt(v)}  [{_src(e.sources.get(f, ''))}]" for f, v in reported] or ["  (none confirmed)"]
    name = " ".join(x for x in (e.details.get("first_name"), e.details.get("family_name")) if x)
    lines += ["", "WOMAN"]
    if name:
        lines.append(f"  - Name: {name}")
    if e.birth_date:
        lines.append(f"  - Date of birth: {e.birth_date}{' (estimated from her age)' if e.birth_date_estimated else ''}")
    lines += questionnaire.handover_lines("anc-registration", e.details, skip={"first_name", "family_name", "wants_reminders"})
    if e.profile:
        lines += ["", "HISTORY AND PROFILE (first contact, ANC.B6)"]
        if e.profile_derived.get("ga_weeks"):
            lines.append(f"  - Gestational age: {e.profile_derived['ga_weeks']} weeks"
                         + (f", EDD {e.profile_derived['edd']}" if e.profile_derived.get("edd") else ""))
        lines += questionnaire.handover_lines("anc-profile", e.profile)
    else:
        lines += ["", "HISTORY AND PROFILE: not collected at this contact"]
    lines += ["", "MEASURED OBSERVATIONS"]
    lines += [f"  - {label(f)}: {fmt(v)}  [{_src(e.sources.get(f, ''))}]" for f, v in measured] or ["  (none confirmed)"]
    lines += ["", "ACTIONS"]
    if e.fired:
        for r in e.fired:
            lines.append(f"  - {r.rule_id} {r.name}: {', '.join(r.reasons)}")
            lines += [f"      -> {a}" for a in r.actions]
    else:
        lines.append("  - No referral rule fired on confirmed data.")
    notes = [n for r in e.results for n in r.notes]
    lines += [f"  ! {n}" for n in notes]
    lines += ["", "Rules are demo rules from the WHO ANC DAK PDF, pending Annex B extraction."]
    return "\n".join(lines)
