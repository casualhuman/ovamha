"""Confirmed encounter -> FHIR R4 transaction Bundle, following the Ovamha Backend
Architecture specification v0.1 (sections 7 resource model, 9 identity, 10 sync,
12 AI provenance, 13 reference transaction).

Resources: Patient, EpisodeOfCare (the pregnancy), Organization (this facility and the
receiving hospital), Practitioner + PractitionerRole (the worker), Device (ASR model;
extraction and safety net), Encounter, Observations, GuidanceResponse, ServiceRequest,
Task, Communication (referral SMS), Consent (national ID check, when given), Provenance.
Only confirmed data is used.

Idempotent upload (SY-02): every resource carries an Ovamha identifier and is posted
with a conditional create (ifNoneExist), so a retried upload never duplicates.
Provenance has no identifier element, so it relies on the transaction being atomic.

Codes: LOINC only where the spec names it (85354-9, 8480-6, 8462-4). Danger signs and
other items use PLACEHOLDER codes in the Ovamha danger-sign/observation code systems,
mapped to DAK quick-check names; SMART ANC codes replace them after Annex extraction.
meta.profile (SMART ANC profiles) and the PlanDefinition version are open items (spec 15.1).

National ID (ID-03, ID-04, 9.3): offline there is no verification service, so only the
fact that an ID document was shown is recorded, with a Consent. The number itself is
never stored, used as a key, or sent.
"""
from __future__ import annotations

import uuid

from .confirm import label
from .encounter import Encounter

FHIR = "https://fhir.ovamha.org"
ID = f"{FHIR}/id"
DANGER_CS = f"{FHIR}/CodeSystem/danger-signs"
OBS_CS = f"{FHIR}/CodeSystem/observations"
CAPTURE_CS = f"{FHIR}/CodeSystem/capture"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
OBS_CAT = "http://terminology.hl7.org/CodeSystem/observation-category"
PART_TYPE = "http://terminology.hl7.org/CodeSystem/provenance-participant-type"
CONTENT_PACK = "Ovamha demo content pack v0.1 (rules from the WHO ANC DAK PDF, pending Annex B extraction)"

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
# Capture method -> Ovamha capture code (spec section 12).
CAPTURE = {"keypad": "keyed", "voice-ai-extracted": "spoken-ai-extracted-confirmed", "ai-safety-net": "ai-flag-confirmed"}


def _urn() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def _ident(system: str, value: str) -> dict:
    return {"system": system, "value": value}


class _Builder:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def add(self, resource: dict, ident: dict | None = None) -> str:
        """Add a resource; with an identifier it is a conditional create (idempotent)."""
        urn = _urn()
        req = {"method": "POST", "url": resource["resourceType"]}
        if ident:
            resource.setdefault("identifier", [])
            if ident not in resource["identifier"]:
                resource["identifier"].insert(0, ident)
            req["ifNoneExist"] = f"identifier={ident['system']}|{ident['value']}"
        self.entries.append({"fullUrl": urn, "resource": resource, "request": req})
        return urn


def _ov_code(system: str, f: str) -> dict:
    return {"coding": [{"system": system, "code": f.replace("_", "-"), "display": label(f)}], "text": label(f)}


def build_bundle(e: Encounter) -> dict:
    b = _Builder()
    c = e.confirmed
    rid = lambda key: _ident(f"{ID}/resource", f"{e.encounter_id}/{key}")  # noqa: E731

    # ---- identity, places, people, devices ----
    patient = {"resourceType": "Patient", "identifier": [_ident(f"{ID}/card", e.card_code)], "gender": "female"}
    if e.birth_date:
        patient["birthDate"] = e.birth_date  # FHIR allows year-only precision for an estimate
        if e.birth_date_estimated:
            patient["_birthDate"] = {"extension": [{"url": f"{FHIR}/StructureDefinition/birthdate-estimated", "valueBoolean": True}]}
    pat = b.add(patient, _ident(f"{ID}/device-uuid", e.woman_id))
    subj = {"reference": pat}
    org = b.add({"resourceType": "Organization", "name": e.facility, "active": True}, _ident(f"{ID}/facility", e.facility_id))
    hosp = b.add({"resourceType": "Organization", "name": e.referral_facility, "active": True},
                 _ident(f"{ID}/facility", e.referral_facility_id))
    prac = b.add({"resourceType": "Practitioner", "active": True}, _ident(f"{ID}/worker", e.worker_id))
    role = b.add({
        "resourceType": "PractitionerRole", "active": True,
        "practitioner": {"reference": prac}, "organization": {"reference": org},
        "code": [{"text": e.worker_role}],
    }, _ident(f"{ID}/worker-role", f"{e.worker_id}@{e.facility_id}"))
    asr = b.add({
        "resourceType": "Device",
        "deviceName": [{"name": e.asr_model, "type": "model-name"}],
        "type": {"text": f"Automatic speech recognition model (language: {e.lang})"},
    }, _ident(f"{ID}/device-model", f"asr/{e.asr_model}/{e.lang}"))
    nlp = b.add({
        "resourceType": "Device",
        "deviceName": [{"name": "Ovamha lexicon extraction and AI safety net v0.1", "type": "model-name"}],
        "type": {"text": "Field extraction and danger-sign safety net"},
    }, _ident(f"{ID}/device-model", "extract-safety-net/v0.1"))

    # ---- the pregnancy and this contact ----
    eoc = b.add({
        "resourceType": "EpisodeOfCare", "status": "active",
        "type": [{"text": "Antenatal care"}],
        "patient": subj, "managingOrganization": {"reference": org},
    }, _ident(f"{ID}/pregnancy", e.episode_id))
    enc = b.add({
        "resourceType": "Encounter", "status": "finished",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "HH", "display": "home health"},
        "subject": subj, "episodeOfCare": [{"reference": eoc}],
        "participant": [{"individual": {"reference": role}}],
        "serviceProvider": {"reference": org},
        "period": {"start": e.at, "end": e.at},
    }, _ident(f"{ID}/encounter", e.code + "-" + e.encounter_id[:8]))
    enc_ref = {"reference": enc}

    # ---- observations, grouped by how they were captured ----
    by_capture: dict[str, list[str]] = {"keyed": [], "spoken-ai-extracted-confirmed": [], "ai-flag-confirmed": []}
    sign_obs: list[str] = []
    measure_obs: list[str] = []

    def obs(key: str, resource: dict, f: str) -> str:
        r = {"resourceType": "Observation", "status": "final", "subject": subj, "encounter": enc_ref,
             "effectiveDateTime": e.at, "performer": [{"reference": role}], **resource}
        u = b.add(r, rid(key))
        src = e.sources.get(f, "keypad").split("+")[0]
        by_capture[CAPTURE.get(src, "keyed")].append(u)
        return u

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
            measure_obs.append(obs(f"bp{suffix}", bp, f"systolic{suffix}"))

    for f, v in c.items():
        if f in DANGER_FIELDS:
            r = {"category": [{"coding": [{"system": OBS_CAT, "code": "exam"}]}], "code": _ov_code(DANGER_CS, f)}
            if isinstance(v, bool):
                r["valueBoolean"] = v
            else:
                r["valueString"] = str(v)  # severity: "severe" / "mild"
            u = obs(f, r, f)
            if v is True or v == "severe":
                sign_obs.append(u)
        elif f in NUMERIC_UNITS and isinstance(v, (int, float)):
            code, unit = NUMERIC_UNITS[f]
            measure_obs.append(obs(f, {"code": _ov_code(OBS_CS, f),
                                       "valueQuantity": {"value": v, "unit": unit, "system": UCUM, "code": code}}, f))
        elif f in ("bleeding_amount", "urine_protein", "severe_pe_symptoms"):
            r = {"code": _ov_code(OBS_CS, f)}
            r["valueBoolean" if isinstance(v, bool) else "valueString"] = v if isinstance(v, bool) else str(v)
            u = obs(f, r, f)
            (measure_obs if f == "urine_protein" else sign_obs if f == "bleeding_amount" else measure_obs).append(u)

    # Obstetric history from registration (keyed by the worker). Placeholder codes until SMART ANC mapping.
    for f, v in e.history.items():
        r = {"category": [{"coding": [{"system": OBS_CAT, "code": "social-history"}]}], "code": _ov_code(OBS_CS, f)}
        if isinstance(v, int):
            r["valueInteger"] = v
        else:
            r["dataAbsentReason"] = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/data-absent-reason", "code": "asked-unknown"}]}
        u = b.add({"resourceType": "Observation", "status": "final", "subject": subj, "encounter": enc_ref,
                   "effectiveDateTime": e.at, "performer": [{"reference": role}], **r}, rid(f"history/{f}"))
        by_capture["keyed"].append(u)

    # ---- rule results ----
    for res in e.results:
        gr = {
            "resourceType": "GuidanceResponse",
            "status": "success" if res.status != "needs_data" else "data-required",
            "subject": subj, "encounter": enc_ref, "occurrenceDateTime": e.at,
            "reasonCode": [{"text": f"{res.rule_id} {res.name}: {res.status}"}],
            "note": [{"text": f"{res.source}. {res.label}."}],
        }
        if res.canonical:
            gr["moduleCanonical"] = res.canonical  # version pin: open item until the content pack is versioned
        else:
            gr["moduleUri"] = f"{FHIR}/rules/{res.rule_id}"
        b.add(gr, rid(f"guidance/{res.rule_id}"))

    # ---- referral: ServiceRequest, Task, Communication (SMS) ----
    if e.referral:
        reasons = sorted({x for r in e.fired for x in r.reasons})
        sr = b.add({
            "resourceType": "ServiceRequest", "status": "active", "intent": "order", "priority": "urgent",
            "code": {"text": "Urgent referral to hospital"},
            "subject": subj, "encounter": enc_ref, "authoredOn": e.at,
            "requester": {"reference": role}, "performer": [{"reference": hosp}],
            "reasonCode": [{"text": t} for t in reasons],
            "reasonReference": [{"reference": u} for u in sign_obs],
            "supportingInfo": [{"reference": u} for u in measure_obs],
        }, _ident(f"{ID}/referral", e.code))
        b.add({
            "resourceType": "Task", "status": e.referral_status, "intent": "order", "priority": "urgent",
            "focus": {"reference": sr}, "for": subj, "encounter": enc_ref, "authoredOn": e.at,
            "requester": {"reference": role}, "owner": {"reference": hosp},
            "description": f"Referral {e.code}: awaiting ACK/FULL by SMS",
        }, _ident(f"{ID}/referral-task", e.code))
        if e.sms:
            comm = {
                "resourceType": "Communication", "status": "completed",
                "basedOn": [{"reference": sr}], "subject": subj, "encounter": enc_ref,
                "category": [{"text": "Referral notice by SMS"}],
                "sender": {"reference": role}, "recipient": [{"reference": hosp}],
                "sent": e.sms["sent"], "payload": [{"contentString": e.sms["text"]}],
            }
            if e.sms.get("channel") == "SIMULATED":
                comm["note"] = [{"text": "SIMULATED SMS: no GSM modem attached (prototype)."}]
            b.add(comm, _ident(f"{ID}/sms", f"{e.code}/referral"))

    # ---- national ID check (optional, consented; no number stored) ----
    if e.national_id and e.national_id.get("consent_at"):
        b.add({
            "resourceType": "Consent", "status": "active",
            "scope": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/consentscope", "code": "patient-privacy"}]},
            "category": [{"text": "Link Ovamha record to national ID"}],
            "patient": subj, "dateTime": e.national_id["consent_at"],
            "performer": [subj], "organization": [{"reference": org}],
            "policy": [{"uri": f"{FHIR}/policy/national-id-linkage"}],
            "provision": {"type": "permit", "purpose": [{"display": f"Identity check: {e.national_id.get('document', 'national ID')} shown; "
                                                                    "number not stored (verify later through the national ID service)"}]},
        }, _ident(f"{ID}/consent", f"{e.woman_id}/national-id"))

    # ---- provenance per capture method (spec section 12) ----
    content_pack = {"role": "source", "what": {"display": CONTENT_PACK}}
    verifier = {"type": {"coding": [{"system": PART_TYPE, "code": "verifier"}]}, "who": {"reference": role}}
    assemblers = {
        "spoken-ai-extracted-confirmed": [asr, nlp],
        "ai-flag-confirmed": [nlp],
        "keyed": [],
    }
    for activity, targets in by_capture.items():
        if not targets:
            continue
        agents = [verifier] + [{"type": {"coding": [{"system": PART_TYPE, "code": "assembler"}]}, "who": {"reference": d}}
                               for d in assemblers[activity]]
        if activity == "keyed":
            agents.insert(0, {"type": {"coding": [{"system": PART_TYPE, "code": "author"}]}, "who": {"reference": role}})
        b.entries.append({
            "fullUrl": _urn(),
            "resource": {
                "resourceType": "Provenance", "target": [{"reference": t} for t in targets], "recorded": e.at,
                "activity": {"coding": [{"system": CAPTURE_CS, "code": activity}]},
                "agent": agents, "entity": [content_pack],
            },
            "request": {"method": "POST", "url": "Provenance"},
        })

    return {"resourceType": "Bundle", "type": "transaction", "entry": b.entries}


def validate(bundle: dict) -> None:
    """Structural validation with fhir.resources (R4B models). Raises on error."""
    from fhir.resources.R4B.bundle import Bundle

    Bundle.model_validate(bundle)
