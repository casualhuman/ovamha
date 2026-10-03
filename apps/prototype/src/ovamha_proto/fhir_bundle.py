"""Confirmed encounter -> FHIR R4 transaction Bundle.

Resources: Patient, Practitioner (worker), Device (ASR model), Encounter,
Observations (BP panel + danger signs), GuidanceResponse, ServiceRequest, Task,
Provenance. Only confirmed data is used.

Codes: the only LOINC codes used are 85354-9 (BP panel), 8480-6 (systolic) and
8462-4 (diastolic). Danger signs and other symptoms use PLACEHOLDER codes in the
Ovamha code system below, mapped to DAK quick-check names; SMART ANC codes replace
them after Annex extraction. No SNOMED or other LOINC codes are invented.

Structural validation uses fhir.resources' R4B models (the library has no pure
R4 package; these resources are unchanged between R4 and R4B). Run
scripts/validate_fhir.sh for the official HL7 validator against base R4 (4.0.1).
"""
from __future__ import annotations

import uuid

from .confirm import label
from .encounter import Encounter

OVAMHA = "https://fhir.ovamha.org"
DANGER_CS = f"{OVAMHA}/CodeSystem/danger-signs"
OBS_CS = f"{OVAMHA}/CodeSystem/observations"
ACTIVITY_CS = f"{OVAMHA}/CodeSystem/provenance-activity"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
OBS_CAT = "http://terminology.hl7.org/CodeSystem/observation-category"
PART_TYPE = "http://terminology.hl7.org/CodeSystem/provenance-participant-type"

DANGER_FIELDS = {
    "vaginal_bleeding", "dizziness", "fainting", "headache", "visual_disturbance", "convulsions", "fever",
    "abdominal_pain", "breathing_difficulty", "unconscious", "vomiting", "reduced_fetal_movement",
    "waters_broken", "swelling", "looks_very_ill", "central_cyanosis", "severe_pain", "imminent_delivery", "labour",
}
NUMERIC_UNITS = {
    "gestational_age_weeks": ("wk", "weeks"),
    "pulse": ("/min", "/min"),
    "temperature": ("Cel", "°C"),
    "fetal_heart_rate": ("/min", "/min"),
}


def _urn() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def _entry(urn: str, resource: dict) -> dict:
    return {"fullUrl": urn, "resource": resource, "request": {"method": "POST", "url": resource["resourceType"]}}


def _ov_code(system: str, f: str) -> dict:
    return {"coding": [{"system": system, "code": f.replace("_", "-"), "display": label(f)}], "text": label(f)}


def build_bundle(e: Encounter) -> dict:
    c = e.confirmed
    pat, prac, dev, enc = _urn(), _urn(), _urn(), _urn()
    subj = {"reference": pat}
    enc_ref = {"reference": enc}
    entries = [
        _entry(pat, {
            "resourceType": "Patient",
            "identifier": [
                {"system": f"{OVAMHA}/sid/woman-id", "value": e.woman_id},
                {"system": f"{OVAMHA}/sid/card-code", "value": e.card_code},
            ],
            "gender": "female",
        }),
        _entry(prac, {
            "resourceType": "Practitioner",
            "identifier": [{"system": f"{OVAMHA}/sid/worker-id", "value": e.worker_id}],
        }),
        _entry(dev, {
            "resourceType": "Device",
            "deviceName": [{"name": e.asr_model, "type": "model-name"}],
            "type": {"text": "Automatic speech recognition model"},
        }),
        _entry(enc, {
            "resourceType": "Encounter",
            "identifier": [{"system": f"{OVAMHA}/sid/encounter-code", "value": e.code}],
            "status": "finished",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "HH", "display": "home health"},
            "subject": subj,
            "participant": [{"individual": {"reference": prac}}],
            "period": {"start": e.at, "end": e.at},
        }),
    ]

    voice_obs: list[str] = []
    keypad_obs: list[str] = []

    def obs(resource: dict, f: str | None = None) -> str:
        u = _urn()
        resource = {"resourceType": "Observation", "status": "final", "subject": subj, "encounter": enc_ref,
                    "effectiveDateTime": e.at, "performer": [{"reference": prac}], **resource}
        entries.append(_entry(u, resource))
        src = e.sources.get(f, "keypad") if f else "keypad"
        (keypad_obs if src.startswith("keypad") else voice_obs).append(u)
        return u

    # Blood pressure panel (confirmed LOINC codes only).
    for suffix, note in (("", None), ("_repeat", "Repeat reading")):
        s, d = c.get(f"systolic{suffix}"), c.get(f"diastolic{suffix}")
        if isinstance(s, (int, float)) and isinstance(d, (int, float)):
            bp = {
                "category": [{"coding": [{"system": OBS_CAT, "code": "vital-signs"}]}],
                "code": {"coding": [{"system": LOINC, "code": "85354-9", "display": "Blood pressure panel with all children optional"}]},
                "component": [
                    {"code": {"coding": [{"system": LOINC, "code": "8480-6", "display": "Systolic blood pressure"}]},
                     "valueQuantity": {"value": s, "unit": "mmHg", "system": UCUM, "code": "mm[Hg]"}},
                    {"code": {"coding": [{"system": LOINC, "code": "8462-4", "display": "Diastolic blood pressure"}]},
                     "valueQuantity": {"value": d, "unit": "mmHg", "system": UCUM, "code": "mm[Hg]"}},
                ],
            }
            if note:
                bp["note"] = [{"text": note}]
            obs(bp, f"systolic{suffix}")

    sign_obs: list[str] = []
    for f, v in c.items():
        if f in DANGER_FIELDS:
            vb = v if isinstance(v, bool) else None
            r = {"category": [{"coding": [{"system": OBS_CAT, "code": "exam"}]}], "code": _ov_code(DANGER_CS, f)}
            if vb is None:
                r["valueString"] = str(v)  # e.g. severity "severe" / "mild"
            else:
                r["valueBoolean"] = vb
            u = obs(r, f)
            if v is True or v == "severe":
                sign_obs.append(u)
        elif f in NUMERIC_UNITS and isinstance(v, (int, float)):
            code, unit = NUMERIC_UNITS[f]
            obs({"code": _ov_code(OBS_CS, f), "valueQuantity": {"value": v, "unit": unit, "system": UCUM, "code": code}}, f)
        elif f in ("bleeding_amount", "urine_protein", "severe_pe_symptoms"):
            r = {"code": _ov_code(OBS_CS, f)}
            r["valueBoolean" if isinstance(v, bool) else "valueString"] = v if isinstance(v, bool) else str(v)
            obs(r, f)

    for res in e.results:
        gr = {
            "resourceType": "GuidanceResponse",
            "identifier": [{"system": f"{OVAMHA}/sid/guidance", "value": f"{e.code}-{res.rule_id}"}],
            "status": "success" if res.status != "needs_data" else "data-required",
            "subject": subj,
            "encounter": enc_ref,
            "occurrenceDateTime": e.at,
            "reasonCode": [{"text": f"{res.rule_id} {res.name}: {res.status}"}],
            "note": [{"text": f"{res.source}. {res.label}."}],
        }
        if res.canonical:
            gr["moduleCanonical"] = res.canonical
        else:
            gr["moduleUri"] = f"{OVAMHA}/rules/{res.rule_id}"
        entries.append(_entry(_urn(), gr))

    if e.referral:
        sr = _urn()
        reasons = sorted({x for r in e.fired for x in r.reasons})
        entries.append(_entry(sr, {
            "resourceType": "ServiceRequest",
            "identifier": [{"system": f"{OVAMHA}/sid/encounter-code", "value": e.code}],
            "status": "active",
            "intent": "order",
            "priority": "urgent",
            "code": {"text": "Urgent referral to hospital"},
            "subject": subj,
            "encounter": enc_ref,
            "authoredOn": e.at,
            "requester": {"reference": prac},
            "reasonCode": [{"text": t} for t in reasons],
            "reasonReference": [{"reference": u} for u in sign_obs],
        }))
        entries.append(_entry(_urn(), {
            "resourceType": "Task",
            "identifier": [{"system": f"{OVAMHA}/sid/encounter-code", "value": e.code}],
            "status": e.referral_status,
            "intent": "order",
            "priority": "urgent",
            "focus": {"reference": sr},
            "for": subj,
            "encounter": enc_ref,
            "authoredOn": e.at,
            "requester": {"reference": prac},
            "description": f"Referral {e.code}: awaiting ACK/FULL by SMS",
        }))

    def provenance(targets: list[str], activity: str, agents: list[dict]) -> None:
        if targets:
            entries.append(_entry(_urn(), {
                "resourceType": "Provenance",
                "target": [{"reference": t} for t in targets],
                "recorded": e.at,
                "activity": {"coding": [{"system": ACTIVITY_CS, "code": activity}]},
                "agent": agents,
            }))

    verifier = {"type": {"coding": [{"system": PART_TYPE, "code": "verifier"}]}, "who": {"reference": prac}}
    provenance(voice_obs, "spoken-ai-extracted-confirmed",
               [verifier, {"type": {"coding": [{"system": PART_TYPE, "code": "assembler"}]}, "who": {"reference": dev}}])
    provenance(keypad_obs, "keypad-entered-confirmed",
               [{"type": {"coding": [{"system": PART_TYPE, "code": "author"}]}, "who": {"reference": prac}}, verifier])

    return {"resourceType": "Bundle", "type": "transaction", "entry": entries}


def validate(bundle: dict) -> None:
    """Structural validation with fhir.resources (R4B models). Raises on error."""
    from fhir.resources.R4B.bundle import Bundle

    Bundle.model_validate(bundle)
