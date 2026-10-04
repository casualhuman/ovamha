"""FHIR Bundle, handover and SMS for the demo scenario."""
import json

import pytest

from ovamha_proto import sms
from ovamha_proto.confirm import Session
from ovamha_proto.encounter import Encounter
from ovamha_proto.extract import extract
from ovamha_proto.fhir_bundle import build_bundle, validate
from ovamha_proto.handover import handover_text
from ovamha_proto.rules import evaluate
from ovamha_proto.safety_net import scan

SCENARIO = "She is 28 weeks pregnant with heavy vaginal bleeding since this morning. She fainted yesterday but is fine now. No fever."


@pytest.fixture
def enc(tmp_path, monkeypatch):
    monkeypatch.setattr(sms, "OUTBOX", tmp_path)
    s = Session()
    ex = extract(SCENARIO, "en")
    s.propose_from_extraction(ex)
    s.propose_flags(scan(ex))
    for f in ("vaginal_bleeding", "bleeding_amount", "fainting"):
        s.confirm(f)
    for f, v in (("gestational_age_weeks", 28), ("systolic", 90), ("diastolic", 60)):
        s.propose_keypad(f, v)
        s.confirm(f)
    confirmed = s.finalise()
    return Encounter(confirmed, dict(s.sources), evaluate(confirmed), "en", s.worker_id, "faster-whisper small int8")


def test_bundle_validates_and_has_required_resources(enc):
    b = build_bundle(enc)
    validate(b)
    types = [e["resource"]["resourceType"] for e in b["entry"]]
    for t in ("Patient", "Encounter", "Observation", "GuidanceResponse", "ServiceRequest", "Task", "Provenance"):
        assert t in types, t
    task = next(e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "Task")
    assert task["status"] == "requested"
    gr = next(e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "GuidanceResponse")
    assert gr["moduleCanonical"] == "http://fhir.org/guides/who/anc-cds/PlanDefinition/ANCDT01"
    prov = [e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "Provenance"]
    assert {p["activity"]["coding"][0]["code"] for p in prov} == {"spoken-ai-extracted-confirmed", "ai-flag-confirmed", "keyed"}
    assert all(p["activity"]["coding"][0]["system"] == "https://fhir.ovamha.org/CodeSystem/capture" for p in prov)


def test_bundle_only_loinc_codes_are_the_confirmed_ones(enc):
    text = json.dumps(build_bundle(enc))
    import re

    loinc = set(re.findall(r'"system": "http://loinc.org", "code": "([^"]+)"', text))
    assert loinc <= {"85354-9", "8480-6", "8462-4"}
    assert "snomed" not in text.lower()


def test_unconfirmed_fever_not_in_bundle_or_handover(enc):
    assert "fever" not in json.dumps(build_bundle(enc)).lower()
    assert "Fever" not in handover_text(enc)


def test_sms_has_code_not_identity(enc):
    t = sms.referral_text(enc)
    assert enc.code in t and "URGENT" in t
    assert enc.woman_id not in t and enc.card_code not in t
    out = sms.send(t)
    assert out.channel == "SIMULATED"


def test_ack_and_full(enc):
    assert sms.handle_reply(f"ACK {enc.code}", enc) == "accepted"
    assert sms.handle_reply("ACK ZZZZ", enc) is None
    assert sms.handle_reply(f"full {enc.code.lower()}", enc) == "rejected"


def test_spec_identifiers_and_conditional_create(enc):
    b = build_bundle(enc)
    pat = next(e for e in b["entry"] if e["resource"]["resourceType"] == "Patient")
    systems = {i["system"] for i in pat["resource"]["identifier"]}
    assert systems == {"https://fhir.ovamha.org/id/device-uuid", "https://fhir.ovamha.org/id/card"}
    assert pat["request"]["ifNoneExist"].startswith("identifier=https://fhir.ovamha.org/id/device-uuid|")
    # SY-02: every resource except Provenance is a conditional create
    for e in b["entry"]:
        if e["resource"]["resourceType"] != "Provenance":
            assert "ifNoneExist" in e["request"], e["resource"]["resourceType"]


def test_referral_resources_per_spec(enc):
    enc.sms = {"text": "OVAMHA REFERRAL X", "sent": enc.at, "channel": "SIMULATED"}
    b = build_bundle(enc)
    validate(b)
    by = {}
    for e in b["entry"]:
        by.setdefault(e["resource"]["resourceType"], []).append(e["resource"])
    for t in ("EpisodeOfCare", "PractitionerRole", "Organization", "Communication"):
        assert t in by, t
    sr = by["ServiceRequest"][0]
    assert sr["supportingInfo"] and sr["reasonReference"] and sr["performer"]
    assert by["Task"][0]["owner"]["reference"].startswith("urn:uuid:")
    assert "SIMULATED" in by["Communication"][0]["note"][0]["text"]


def test_national_id_number_never_in_bundle(enc):
    enc.national_id = {"document": "Sierra Leone NIN card", "method": "document-shown", "verified": False, "consent_at": enc.at}
    b = build_bundle(enc)
    validate(b)
    consent = [e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "Consent"]
    assert len(consent) == 1 and consent[0]["status"] == "active"
