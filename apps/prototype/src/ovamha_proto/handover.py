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
    "voice-ai-classifier": "reported (voice, AI text classifier, confirmed)",
    "ai-safety-net": "raised by AI safety net, confirmed by worker",
    "ai-classifier": "raised by AI text classifier, confirmed by worker",
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
        f"MATERNALSAVE REFERRAL FORM / HANDOVER  {e.code}  ({title})",
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
    if e.management:
        lines += ["", "GUIDELINE MANAGEMENT SHOWN TO THE WORKER"]
        lines += [f"  - {m['title']} [{m['cite']}]" for m in e.management]
    if e.routine:
        lines += ["", f"CARE DUE AT CONTACT {e.routine['contact']} (around {e.routine['week']} weeks)"]
        lines += [f"  - {t}" for t in e.routine["items"] + e.routine.get("tests", [])]
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


def letter(e: Encounter) -> dict:
    """Printable referral letter. Elements follow the guideline's referral form requirements:
    clinical findings, treatment given before referral, specific reasons for referral, and a
    feedback section for the receiving facility (two-way referral)."""
    d = e.details
    name = " ".join(x for x in (d.get("first_name"), d.get("family_name")) if x) or "Name not recorded"
    ga = e.confirmed.get("gestational_age_weeks") or e.profile_derived.get("ga_weeks")
    p = e.profile
    obstetric = []
    if isinstance(p.get("gravida"), int):
        obstetric.append(f"Gravida {p['gravida']}")
    if isinstance(p.get("live_births"), int):
        obstetric.append(f"{p['live_births']} live birth(s)")
    complaints = [f"{label(f)}: {fmt(v)}" for f, v in e.confirmed.items()
                  if f not in KEYPAD_FIELDS and f not in ("urine_protein", "severe_pe_symptoms") and v not in (False,)]
    c = e.confirmed
    findings = []
    for suffix, name in (("", "BP"), ("_repeat", "Repeat BP")):
        if isinstance(c.get(f"systolic{suffix}"), (int, float)) and isinstance(c.get(f"diastolic{suffix}"), (int, float)):
            findings.append(f"{name} {c[f'systolic{suffix}']}/{c[f'diastolic{suffix}']} mmHg")
    units = {"pulse": "/min", "temperature": " °C", "fetal_heart_rate": "/min", "gestational_age_weeks": " weeks"}
    for f, unit in units.items():
        if isinstance(c.get(f), (int, float)):
            findings.append(f"{label(f).split(' (')[0]} {c[f]}{unit}")
    for f in ("urine_protein", "severe_pe_symptoms"):
        if f in c:
            findings.append(f"{label(f)}: {fmt(c[f])}")
    history = questionnaire.handover_lines("anc-profile", {k: v for k, v in p.items()
                                                           if k in ("past_complications", "chronic_conditions", "allergies", "current_medications", "past_surgeries")})
    # National wording first; drop a WHO reason already covered by it (e.g. "Fever" inside "High fever").
    national = list(dict.fromkeys(x for a in e.advice for x in a.reasons))
    who = [x for r in e.fired for x in r.reasons if not any(x.lower() in n.lower() for n in national)]
    reasons = national + list(dict.fromkeys(who))
    basis = list(dict.fromkeys([f"WHO ANC DAK {r.rule_id} {r.name}" for r in e.fired] + [f"{a.source}: {a.cite}" for a in e.advice]))
    choice = (e.decision or {}).get("choice")
    st = e.referral_steps
    return {
        "date": e.at, "ref": e.code, "card": _card(e), "urgent": e.urgent, "type": DECISION_TEXT.get(choice, "Referral"),
        "from": {"facility": e.facility, "level": e.facility_level, "worker": e.worker_name or e.worker_id, "role": e.worker_role},
        "to": {"facility": e.referral_facility, "level": "CEmONC"},
        "patient": {"name": name, "age": _age_text(e), "card": _card(e), "community": d.get("address"), "phone": d.get("phone"),
                    "ga": f"About {ga} weeks" if ga else "Not known", "edd": e.profile_derived.get("edd"), "obstetric": ", ".join(obstetric)},
        "reasons": reasons or ["See clinical findings"],
        "complaints": complaints, "findings": findings,
        "history": [h.strip(" -") for h in history],
        "treatment": st.get("checklist", []),
        "consent": "Given" if st.get("consent") else ("Not given" if st else "Not applicable"),
        "call": {"called": st.get("call_time"), "arrived": st.get("ambulance_time")},
        "worker_reason": (e.decision or {}).get("reason"),
        "basis": basis,
        "request": ("Please receive her for urgent assessment and management." if e.urgent
                    else "Please assess her and advise on the plan of care and place of delivery."),
    }
