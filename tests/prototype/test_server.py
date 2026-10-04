"""End-to-end through the HTTP API: login -> extract -> confirm -> measure -> finish -> ACK."""
import json

import pytest
from fastapi.testclient import TestClient

from ovamha_proto import auth, server, sms

REG = {"notice_given": True, "national_id": "none", "age_years": 24, "details": {"first_name": "Mariama"}}
SCENARIO = "She is 28 weeks pregnant and she has heavy vaginal bleeding since this morning. She fainted yesterday but is fine now. No fever."


@pytest.fixture
def client(tmp_path, monkeypatch):
    salt, h = auth.hash_pin("123456")
    f = tmp_path / "users.json"
    f.write_text(json.dumps({"users": [{"username": "test", "worker_id": "nurse-test", "display_name": "Nurse Test", "role": "Nurse",
                                        "facility": "Test CHP", "languages": ["kri", "en"], "pin_salt": salt, "pin_hash": h}]}))
    monkeypatch.setattr(auth, "USERS_FILE", f)
    monkeypatch.setattr(auth, "_failures", {})
    monkeypatch.setattr(sms, "OUTBOX", tmp_path)
    monkeypatch.setenv("OVAMHA_DATA", str(tmp_path))
    monkeypatch.setenv("OVAMHA_DETECTOR", "rules")  # flow tests must not depend on the (uncommitted) classifier model
    c = TestClient(server.app)
    token = c.post("/api/login", json={"username": "test", "pin": "123456"}).json()["token"]
    c.headers["Authorization"] = f"Bearer {token}"
    return c


def test_requires_login():
    assert TestClient(server.app).get("/api/state").status_code == 401


def test_wrong_pin_rejected(client):
    r = TestClient(server.app).post("/api/login", json={"username": "test", "pin": "000000"})
    assert r.status_code == 401


def test_full_scenario(client):
    card = client.post("/api/woman/new", json=REG).json()["woman"]["card_code"]
    st = client.post("/api/extract", json={"transcript": SCENARIO, "lang": "en"}).json()
    fields = {i["field"]: i for i in st["items"]}
    assert fields["vaginal_bleeding"]["value"] is True
    assert fields["fainting"]["source"] == "ai-safety-net"
    assert not any(i["confirmed"] for i in st["items"])

    for f in ("vaginal_bleeding", "bleeding_amount", "fainting"):
        st = client.post("/api/confirm", json={"field": f}).json()
    assert st["preview"]["danger"] is True

    for f, v in (("systolic", "90"), ("diastolic", "60")):
        assert client.post("/api/measure", json={"field": f, "value": v}).status_code == 200
        client.post("/api/confirm", json={"field": f})

    a = client.post("/api/finish").json()
    assert a["suggestion"] == "urgent_referral" and "sms" not in a  # the app suggests; nothing is sent yet
    assert any("Table 3.3" in x["cite"] for x in a["advice"])
    d = client.post("/api/decision", json={"choice": "urgent"}).json()
    assert d["next"] == "referral" and set(d["isbar"]) == {"I", "S", "B", "A", "R"}
    r = client.post("/api/referral/complete", json={"consent": True, "checklist": [0, 1], "call_time": "10:42"}).json()
    assert r["referral"] and r["urgent"] and r["valid"]["ok"]
    assert r["card_code"] == card and card in r["handover"] and "I  Identification" in r["handover"]
    assert "Fever" not in r["handover"].split("GUIDELINE ADVICE")[0]  # proposed, never confirmed -> discarded
    assert r["sms"]["channel"] == "SIMULATED" and r["code"] in r["sms"]["text"]
    assert card.replace("-", "") not in r["sms"]["text"]  # SMS carries the encounter code only

    out = client.post("/api/sms/reply", json={"text": f"ACK {r['code']}"}).json()
    assert out["status"] == "accepted"


def _assess_bleeding(client):
    client.post("/api/woman/new", json=REG)
    client.post("/api/extract", json={"transcript": "heavy bleeding", "lang": "en"})
    client.post("/api/confirm", json={"field": "vaginal_bleeding"})
    return client.post("/api/finish").json()


def test_declining_a_suggested_referral_needs_a_reason(client):
    _assess_bleeding(client)
    assert client.post("/api/decision", json={"choice": "none"}).status_code == 422
    r = client.post("/api/decision", json={"choice": "none", "reason": "Bleeding stopped; reviewed by midwife on site"}).json()
    assert r["next"] == "done" and not r["referral"] and r["sms"] is None
    assert "Reason: Bleeding stopped" in r["handover"]
    types = [e["resource"]["resourceType"] for e in r["bundle"]["entry"]]
    assert "ServiceRequest" not in types and "GuidanceResponse" in types


def test_woman_refuses_referral(client):
    _assess_bleeding(client)
    client.post("/api/decision", json={"choice": "urgent"})
    r = client.post("/api/referral/complete", json={"consent": False}).json()
    assert not r["referral"] and r["sms"] is None and "NOT given" in r["handover"]


def test_planned_referral_is_routine_and_sends_no_sms(client):
    client.post("/api/woman/new", json=REG)
    client.post("/api/profile", json={"answers": dict(PROFILE, lmp=None, ga_source="unknown")})
    client.post("/api/extract", json={"transcript": "no bleeding", "lang": "en"})
    client.post("/api/confirm", json={"field": "vaginal_bleeding"})
    a = client.post("/api/finish").json()
    assert a["suggestion"] == "plan_cemonc_delivery"  # previous pre-eclampsia in PROFILE (Table 3.4)
    r = client.post("/api/decision", json={"choice": "planned"}).json()
    sr = next(e["resource"] for e in r["bundle"]["entry"] if e["resource"]["resourceType"] == "ServiceRequest")
    assert sr["priority"] == "routine" and r["sms"] is None


def test_implausible_measurement_rejected(client):
    r = client.post("/api/measure", json={"field": "systolic", "value": "0"})
    assert r.status_code == 422 and "looks wrong" in r.json()["detail"]


def test_severity_confirmation(client):
    client.post("/api/extract", json={"transcript": "she has abdominal pain", "lang": "en"})
    st = client.post("/api/confirm", json={"field": "abdominal_pain", "value": "severe"}).json()
    assert st["preview"]["danger"] is True


def test_static_app_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "app.js" in r.text


def test_finish_requires_woman(client):  # noqa: D103
    assert client.post("/api/finish").status_code == 409


def test_returning_woman_by_card(client):
    card = client.post("/api/woman/new", json=REG).json()["woman"]["card_code"]
    client.post("/api/encounter/new", json={"lang": "en"})
    st = client.post("/api/woman/find", json={"card_code": card.lower()}).json()
    assert st["woman"]["card_code"] == card
    assert client.post("/api/woman/find", json={"card_code": "AAA-AAA"}).status_code == 404


def test_speak_prompt(client):
    r = client.post("/api/speak", json={"prompt": "ask_bp", "lang": "en"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/wav"


def test_register_requires_birth_info(client):
    r = client.post("/api/woman/new", json={"notice_given": True, "national_id": "none", "details": {"first_name": "A"}})
    assert r.status_code == 422 and "date of birth" in r.json()["detail"].lower()


PROFILE = {
    "pregnancy_confirmed": "test_positive", "ga_source": "lmp", "lmp": None,
    "gravida": 3, "live_births": 2, "stillbirths": 0, "miscarriages": 0, "last_birth_preterm": "no",
    "past_complications": ["pre_eclampsia"], "chronic_conditions": ["none"], "allergies": ["unknown"],
    "past_surgeries": ["none"], "current_medications": ["iron_folic"], "ttcv_doses": "unknown",
    "caffeine_high": "no", "alcohol_substance": "no", "tobacco": "none", "partner_hiv": "unknown",
}


def test_registration_and_profile_flow_into_bundle_and_handover(client):
    from datetime import date, timedelta

    st = client.post("/api/woman/new", json={"notice_given": True, "national_id": "nin", "consent": True, "age_years": 24,
                                             "details": {"first_name": "Mariama", "phone": "+232 76 123456", "wants_reminders": "yes"}}).json()
    assert st["needs_profile"] is True and st["woman"]["name"] == "Mariama"
    prof = dict(PROFILE, lmp=(date.today() - timedelta(weeks=20)).isoformat())
    st = client.post("/api/profile", json={"answers": prof}).json()
    assert st["needs_profile"] is False and st["woman"]["profile_derived"]["ga_weeks"] == 20.0
    client.post("/api/extract", json={"transcript": "heavy bleeding", "lang": "en"})
    client.post("/api/confirm", json={"field": "vaginal_bleeding"})
    client.post("/api/finish")
    client.post("/api/decision", json={"choice": "urgent"})
    r = client.post("/api/referral/complete", json={"consent": True}).json()
    assert r["valid"]["ok"], r["valid"]
    entries = [e["resource"] for e in r["bundle"]["entry"]]
    pat = next(x for x in entries if x["resourceType"] == "Patient")
    assert pat["name"][0]["given"] == ["Mariama"] and pat["telecom"][0]["value"] == "+232 76 123456"
    assert len(pat["birthDate"]) == 4 and pat["_birthDate"]["extension"][0]["valueBoolean"] is True
    lmp = [x for x in entries if x["resourceType"] == "Observation" and x["code"]["coding"][0].get("code") == "8665-2"]
    assert len(lmp) == 1
    hiv = next(x for x in entries if x["resourceType"] == "Observation" and any(c.get("code") == "partner_hiv" for c in x["code"]["coding"]))
    assert hiv["meta"]["security"][0]["code"] == "R" and hiv["dataAbsentReason"]
    assert "Mariama" not in r["sms"]["text"]  # SMS never carries her name
    assert "Gestational age: 20.0 weeks" in r["handover"] and "Pre-eclampsia" in r["handover"]
    assert "Contact 3 at 26 weeks" in r["handover"]  # next contact from the national schedule (Table 3.2)


def test_profile_rejects_missing_answers(client):
    client.post("/api/woman/new", json=REG)
    r = client.post("/api/profile", json={"answers": {"ga_source": "lmp"}})
    assert r.status_code == 422 and "please answer" in r.json()["detail"]


def test_registration_requires_first_name(client):
    r = client.post("/api/woman/new", json={"notice_given": True, "national_id": "none", "age_years": 24, "details": {}})
    assert r.status_code == 422 and "First name" in r.json()["detail"]


def test_speak_question_and_option(client):
    for body in ({"questionnaire": "anc-profile", "question": "gravida"}, {"questionnaire": "anc-profile", "question": "tobacco", "option": "exposed"}):
        r = client.post("/api/speak", json=body | {"lang": "en"})
        assert r.status_code == 200, body


def test_routine_visit_sends_reminder_only_with_consent(client):
    reg = {**REG, "details": {"first_name": "Mariama", "phone": "+23276000999", "wants_reminders": "yes"}, "lmp": None}
    client.post("/api/woman/new", json=reg)
    client.post("/api/measure", json={"field": "gestational_age_weeks", "value": "30"})
    client.post("/api/confirm", json={"field": "gestational_age_weeks"})
    client.post("/api/finish")
    r = client.post("/api/decision", json={"choice": "none"}).json()
    assert r["reminder"]["to"] == "+23276000999" and "Mariama" not in r["reminder"]["text"]
    log = client.get("/api/sms/log").json()
    assert log["messages"][-1]["kind"] == "reminder"


def test_no_reminder_without_consent(client):
    client.post("/api/woman/new", json={**REG, "details": {"first_name": "Mariama", "phone": "+23276000999", "wants_reminders": "no"}})
    client.post("/api/measure", json={"field": "gestational_age_weeks", "value": "30"})
    client.post("/api/confirm", json={"field": "gestational_age_weeks"})
    client.post("/api/finish")
    assert client.post("/api/decision", json={"choice": "none"}).json()["reminder"] is None
