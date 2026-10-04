"""Handover text: reported symptoms, measured observations and actions, kept separate.

Contains confirmed fields only (the Encounter is built from Session.finalise()).
"""
from __future__ import annotations

from .confirm import KEYPAD_FIELDS, fmt, label
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
