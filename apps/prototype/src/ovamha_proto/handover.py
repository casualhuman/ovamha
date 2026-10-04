"""Referral form and handover, in the iSBAR order the Sierra Leone guideline asks for
(Identification, Situation, Background, Assessment, Recommendation).

Reported symptoms, measured observations, guideline advice and the worker's decision are
kept separate. Contains confirmed fields only (the Encounter is built from Session.finalise()).
"""
from __future__ import annotations

from . import questionnaire
from .confirm import KEYPAD_FIELDS, fmt, label
from .encounter import Encounter

SOURCE_TEXT = {
    "voice-ai-extracted": "reported (voice, confirmed)",
    "ai-safety-net": "raised by AI safety net, confirmed by worker",
    "keypad": "entered on keypad",
}
DECISION_TEXT = {"urgent": "Urgent referral", "planned": "Planned referral (not an emergency)", "none": "No referral at this contact"}


def _src(s: str) -> str:
    base = SOURCE_TEXT.get(s.split("+")[0], s)
    return base + ("; corrected by worker" if s.endswith("worker-corrected") else "")


def _card(e: Encounter) -> str:
    return f"{e.card_code[:3]}-{e.card_code[3:]}"


def _age_text(e: Encounter) -> str:
    if not e.birth_date:
        return "age not recorded"
    return f"born about {e.birth_date} (estimated)" if e.birth_date_estimated else f"born {e.birth_date}"


def isbar(e: Encounter) -> dict:
    """Short iSBAR for the referral call (read aloud to the call centre) and the top of the referral form."""
    name = " ".join(x for x in (e.details.get("first_name"), e.details.get("family_name")) if x) or "a pregnant woman"
    ga = e.confirmed.get("gestational_age_weeks") or e.profile_derived.get("ga_weeks")
    signs = [label(f) for f, v in e.confirmed.items() if f not in KEYPAD_FIELDS and v not in (False, "mild", "light")
             and f not in ("bleeding_amount", "urine_protein", "severe_pe_symptoms")]
    risks = sorted({r for a in e.advice if a.kind not in ("urgent_referral", "check_now") for r in a.reasons})
    vitals = []
    if isinstance(e.confirmed.get("systolic"), (int, float)):
        vitals.append(f"BP {e.confirmed['systolic']}/{e.confirmed.get('diastolic', '?')}")
    for f, unit in (("pulse", "/min"), ("temperature", "°C"), ("fetal_heart_rate", "/min fetal heart")):
        if isinstance(e.confirmed.get(f), (int, float)):
            vitals.append(f"{label(f).split(' (')[0]} {e.confirmed[f]}{unit if f != 'fetal_heart_rate' else ''}")
    urgent = [a.title for a in e.advice if a.kind == "urgent_referral"] + [r.name for r in e.fired]
    decision = DECISION_TEXT.get((e.decision or {}).get("choice"), "Decision pending")
    return {
        "I": f"{e.worker_name or e.worker_role + ' ' + e.worker_id} ({e.worker_role}) at {e.facility} ({e.facility_level}). Referral code {e.code}, card {_card(e)}.",
        "S": f"{name}, {_age_text(e)}" + (f", about {ga} weeks pregnant" if ga else "") + ". "
             + (f"Confirmed: {', '.join(signs)}." if signs else "No danger sign confirmed."),
        "B": (f"Risk factors: {', '.join(risks)}." if risks else "No high-risk factors recorded.")
             + ("" if e.profile else " First-contact history not yet collected."),
        "A": (f"Measured: {', '.join(vitals)}. " if vitals else "No measurements. ")
             + (f"Guideline: {', '.join(dict.fromkeys(urgent))}." if urgent else ""),
        "R": f"{decision}." + (" Requesting ambulance and urgent assessment at a CEmONC facility." if (e.decision or {}).get("choice") == "urgent" else ""),
    }


def handover_text(e: Encounter) -> str:
    sb = isbar(e)
    reported = [(f, v) for f, v in e.confirmed.items() if f not in KEYPAD_FIELDS]
    measured = [(f, v) for f, v in e.confirmed.items() if f in KEYPAD_FIELDS]
    title = DECISION_TEXT.get((e.decision or {}).get("choice"), "Assessment").upper()
    lines = [
        f"OVAMHA REFERRAL FORM / HANDOVER  {e.code}  ({title})",
        f"Card number: {_card(e)}   Time: {e.at}   From: {e.facility} ({e.facility_level})   Worker: {e.worker_id}",
        "",
        f"I  Identification: {sb['I']}",
        f"S  Situation:      {sb['S']}",
        f"B  Background:     {sb['B']}",
        f"A  Assessment:     {sb['A']}",
        f"R  Recommendation: {sb['R']}",
        "",
        "REPORTED SYMPTOMS",
    ]
    lines += [f"  - {label(f)}: {fmt(v)}  [{_src(e.sources.get(f, ''))}]" for f, v in reported] or ["  (none confirmed)"]
    lines += ["", "MEASURED OBSERVATIONS"]
    lines += [f"  - {label(f)}: {fmt(v)}  [{_src(e.sources.get(f, ''))}]" for f, v in measured] or ["  (none confirmed)"]
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
    lines += ["", "GUIDELINE ADVICE (suggestions to the health worker)"]
    for r in e.fired:
        lines.append(f"  - WHO DAK {r.rule_id} {r.name}: {', '.join(r.reasons)}")
    for a in e.advice:
        lines.append(f"  - {a.title}: {', '.join(a.reasons)} -> {a.recommendation} [{a.cite}]")
    if not e.fired and not e.advice:
        lines.append("  - No referral suggested on confirmed data.")
    lines += [f"  ! {n}" for r in e.results for n in r.notes]
    lines += ["", "DECISION (by the health worker)"]
    if e.decision:
        lines.append(f"  - {DECISION_TEXT[e.decision['choice']]} by {e.decision['by']} at {e.decision['at']}"
                     + (f". Reason: {e.decision['reason']}" if e.decision.get("reason") else ""))
    else:
        lines.append("  - Pending")
    st = e.referral_steps
    if st:
        lines.append(f"  - Woman's consent to referral: {'given' if st.get('consent') else 'NOT given'}")
        lines += [f"  - Done before referral: {x}" for x in st.get("checklist", [])]
        if st.get("call_time"):
            lines.append(f"  - Ambulance called at {st['call_time']}" + (f"; arrived {st['ambulance_time']}" if st.get("ambulance_time") else ""))
    if e.next_contact.get("text"):
        lines += ["", f"NEXT CONTACT: {e.next_contact['text']}"]
    lines += ["", "WHO DAK rules are demo rules pending Annex B extraction; national advice from the Sierra Leone",
              "Integrated Obstetric and Newborn Care Guideline (2026 draft)."]
    return "\n".join(lines)
