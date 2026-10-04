"""Demo decision rules from the WHO DAK for antenatal care (2021) PDF.

DEMO RULES, PENDING ANNEX B EXTRACTION. These are transcribed from the DAK PDF
for the hackathon prototype and must be replaced by the Annex B decision tables.

Rules are pure functions on *confirmed* data only (see confirm.py). A value
that is missing or "unknown" is never treated as normal: if a rule needs it,
the rule returns status "needs_data" and names what to ask for.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

UNKNOWN = "unknown"
DEMO_LABEL = "Demo rule from the WHO ANC DAK PDF, pending Annex B extraction"

# DAK Fig. 11 quick check: any of these present means urgent referral.
DT01_SIGNS = {
    "unconscious": "Unconscious",
    "convulsions": "Convulsing",
    "vaginal_bleeding": "Vaginal bleeding",
    "severe_abdominal_pain": "Severe abdominal pain",
    "looks_very_ill": "Looks very ill",
    "headache_with_visual_disturbance": "Severe headache with visual disturbance",
    "severe_breathing_difficulty": "Severe difficulty breathing",
    "central_cyanosis": "Central cyanosis",
    "fever": "Fever",
    "severe_vomiting": "Severe vomiting",
    "severe_pain": "Severe pain",
    "imminent_delivery": "Imminent delivery",
    "labour": "Labour",
}

PROTEIN_LEVELS = ("negative", "trace", "+", "++", "+++")


@dataclass
class RuleResult:
    rule_id: str
    name: str
    status: str  # "fired" | "not_fired" | "needs_data"
    reasons: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    source: str = ""
    canonical: str = ""
    label: str = DEMO_LABEL

    @property
    def fired(self) -> bool:
        return self.status == "fired"


def _known(v) -> bool:
    return v is not None and v != UNKNOWN


# Symptom fields whose quick-check sign requires "severe": value is True/False/"severe"/"mild".
SEVERITY_FIELDS = {
    "abdominal_pain": "severe_abdominal_pain",
    "breathing_difficulty": "severe_breathing_difficulty",
    "vomiting": "severe_vomiting",
}


def derived_signs(c: dict) -> dict:
    """Map confirmed symptom fields onto the DAK quick-check signs.

    Headache + visual disturbance -> combined sign. A symptom confirmed present
    but with unconfirmed severity maps to UNKNOWN, never to "not severe".
    """
    d = dict(c)
    for f, sign in SEVERITY_FIELDS.items():
        if sign in d or f not in c:
            continue
        v = c[f]
        d[sign] = True if v == "severe" else False if v in (False, "mild") else UNKNOWN
    h, v = c.get("headache"), c.get("visual_disturbance")
    h = True if h in ("severe", "mild") else h  # headache may carry a confirmed severity
    if h is True and v is True:
        d["headache_with_visual_disturbance"] = True
    elif h is False or v is False:
        d["headache_with_visual_disturbance"] = False
    elif "headache" in c or "visual_disturbance" in c:
        d["headache_with_visual_disturbance"] = UNKNOWN
    return d


def anc_dt01_danger_signs(confirmed: dict) -> RuleResult:
    """ANC.DT.01 Danger signs requiring referral (DAK Fig. 11 quick check)."""
    c = derived_signs(confirmed)
    r = RuleResult(
        rule_id="ANC.DT.01",
        name="Danger signs requiring referral",
        status="not_fired",
        source="WHO DAK for antenatal care (2021), Fig. 11 quick check",
        canonical="http://fhir.org/guides/who/anc-cds/PlanDefinition/ANCDT01",
    )
    present = [label for key, label in DT01_SIGNS.items() if c.get(key) is True]
    if present:
        r.status = "fired"
        r.reasons = present
        r.actions = ["Urgent referral to hospital", "Rapid assessment", "Call for help"]
        return r
    # No sign present: only "not_fired" if every sign was explicitly answered "no".
    r.missing = [key for key in DT01_SIGNS if c.get(key) is not False]
    if r.missing:
        r.status = "needs_data"
    return r


def _in_pe_range(sys_, dia) -> bool:
    return (140 <= sys_ < 160) or (90 <= dia < 110)


def pre_eclampsia(confirmed: dict) -> RuleResult:
    """Pre-eclampsia (DAK Table 12 worked example; ANC.DT.16 in Table 12, ANC.DT.17 in Table 10).

    IF systolic 140 to <160 OR diastolic 90 to <110, AND a repeat reading in the same
    range, AND no symptoms of severe pre-eclampsia, AND urine protein ++ or +++
    -> pre-eclampsia; refer urgently to hospital; revise birth plan.
    """
    c = confirmed
    r = RuleResult(
        rule_id="ANC.PE",
        name="Pre-eclampsia",
        status="not_fired",
        source="WHO DAK for antenatal care (2021), Table 12 worked example (ANC.DT.16 / Table 10 ANC.DT.17)",
    )
    sys_, dia = c.get("systolic"), c.get("diastolic")
    if not (_known(sys_) and _known(dia)):
        r.status = "needs_data"
        r.missing = [k for k in ("systolic", "diastolic") if not _known(c.get(k))]
        return r
    if not _in_pe_range(sys_, dia):
        if sys_ >= 160 or dia >= 110:
            r.notes.append(
                "BP at or above 160/110 is outside this rule; the severe hypertension "
                "rule is pending Annex B extraction. Follow national guidelines."
            )
        return r

    r.reasons.append(f"BP {sys_}/{dia} in range 140-<160 / 90-<110")
    missing = []
    rs, rd = c.get("systolic_repeat"), c.get("diastolic_repeat")
    if not (_known(rs) and _known(rd)):
        missing += [k for k in ("systolic_repeat", "diastolic_repeat") if not _known(c.get(k))]
    elif not _in_pe_range(rs, rd):
        return r  # repeat reading not in the same range
    else:
        r.reasons.append(f"Repeat BP {rs}/{rd} in the same range")

    severe = c.get("severe_pe_symptoms")
    if not _known(severe):
        missing.append("severe_pe_symptoms")
    elif severe is True:
        r.notes.append(
            "Symptoms of severe pre-eclampsia present: outside this rule; the severe "
            "pre-eclampsia rule is pending Annex B extraction. Refer urgently."
        )
        return r

    protein = c.get("urine_protein")
    if not _known(protein):
        missing.append("urine_protein")
    elif protein not in ("++", "+++"):
        return r
    else:
        r.reasons.append(f"Urine protein {protein}")

    if missing:
        r.status = "needs_data"
        r.missing = missing
        return r
    r.status = "fired"
    r.actions = ["Pre-eclampsia: refer urgently to hospital", "Revise birth plan"]
    return r


ALL_RULES = (anc_dt01_danger_signs, pre_eclampsia)


def evaluate(confirmed: dict) -> list[RuleResult]:
    return [rule(confirmed) for rule in ALL_RULES]


def questions_to_ask(results: list[RuleResult]) -> list[str]:
    """Tiered history: if a danger sign is present, refer immediately and ask nothing more.

    Otherwise ask only for the values the current rules need.
    """
    if any(r.rule_id == "ANC.DT.01" and r.fired for r in results):
        return []
    seen: list[str] = []
    for r in results:
        for m in r.missing:
            if m not in seen:
                seen.append(m)
    return seen


def gestational_age_weeks(lmp: date, today: date) -> float:
    """GA (weeks) = (today - LMP) / 7."""
    return (today - lmp).days / 7


def edd(lmp: date) -> date:
    """EDD = LMP + 280 days."""
    return lmp + timedelta(days=280)
