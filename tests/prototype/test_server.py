"""End-to-end through the HTTP API: login -> extract -> confirm -> measure -> finish -> ACK."""
import json

import pytest
from fastapi.testclient import TestClient

from ovamha_proto import auth, server, sms

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
    card = client.post("/api/woman/new").json()["woman"]["card_code"]
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

    r = client.post("/api/finish").json()
    assert r["referral"] and r["valid"]["ok"]
    assert r["card_code"] == card and card in r["handover"]
    assert card.replace("-", "") not in r["sms"]["text"]  # SMS carries the encounter code only
    assert "Fever" not in r["handover"]  # proposed, never confirmed -> discarded
    assert r["sms"]["channel"] == "SIMULATED" and r["code"] in r["sms"]["text"]

    out = client.post("/api/sms/reply", json={"text": f"ACK {r['code']}"}).json()
    assert out["status"] == "accepted"


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


def test_finish_requires_woman(client):
    assert client.post("/api/finish").status_code == 409


def test_returning_woman_by_card(client):
    card = client.post("/api/woman/new").json()["woman"]["card_code"]
    client.post("/api/encounter/new", json={"lang": "en"})
    st = client.post("/api/woman/find", json={"card_code": card.lower()}).json()
    assert st["woman"]["card_code"] == card
    assert client.post("/api/woman/find", json={"card_code": "AAA-AAA"}).status_code == 404


def test_speak_prompt(client):
    r = client.post("/api/speak", json={"prompt": "ask_bp", "lang": "en"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/wav"
