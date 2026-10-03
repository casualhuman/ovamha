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
    assert {p["activity"]["coding"][0]["code"] for p in prov} == {"spoken-ai-extracted-confirmed", "keypad-entered-confirmed"}


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
