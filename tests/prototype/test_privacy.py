"""Privacy controls: encryption at rest, audit trail, audio deletion, idle sign-out, privacy notice,
her right to see her record, anonymised export. See docs/privacy/README.md for the sources."""
import io
import json
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ovamha_proto import audit, auth, registry, secure_store, server, sms, sync

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OVAMHA_DATA", str(tmp_path))
    monkeypatch.delenv("OVAMHA_KEY", raising=False)
    return tmp_path


@pytest.fixture
def client(tmp_path, monkeypatch):
    salt, h = auth.hash_pin("123456")
    f = tmp_path / "users.json"
    f.write_text(json.dumps({"users": [{"username": "test", "worker_id": "nurse-test", "display_name": "Nurse Test", "role": "Nurse",
                                        "facility": "Test CHP", "languages": ["en"], "pin_salt": salt, "pin_hash": h}]}))
    monkeypatch.setattr(auth, "USERS_FILE", f)
    monkeypatch.setattr(auth, "_failures", {})
    monkeypatch.setattr(sms, "OUTBOX", tmp_path)
    monkeypatch.setenv("OVAMHA_DETECTOR", "rules")
    c = TestClient(server.app)
    c.headers["Authorization"] = "Bearer " + c.post("/api/login", json={"username": "test", "pin": "123456"}).json()["token"]
    return c


REG = {"notice_given": True, "national_id": "none", "age_years": 24, "details": {"first_name": "Mariama", "phone": "+23276000000"}}


# ---- encryption at rest
def test_registry_is_encrypted_on_disk(data_dir):
    registry.register("n", age_years=25, details={"first_name": "Mariama"})
    raw = (data_dir / "registry.json").read_bytes()
    assert secure_store.is_encrypted(data_dir / "registry.json") and b"Mariama" not in raw
    for f in ("device.key", "registry.json"):
        assert (data_dir / f).stat().st_mode & 0o077 == 0, f  # owner-only files
    assert data_dir.stat().st_mode & 0o077 == 0


def test_plain_registry_from_older_version_is_read_then_encrypted(data_dir):
    w = registry.register("n", age_years=25)
    data = registry._load()
    (data_dir / "registry.json").write_text(json.dumps(data))  # simulate an old plaintext file
    assert registry.find(w.card_code)[0].woman_id == w.woman_id
    registry.record_visit(w.card_code)
    assert secure_store.is_encrypted(data_dir / "registry.json")


def test_sms_log_and_outbox_are_encrypted(data_dir, monkeypatch):
    monkeypatch.setattr(sms, "OUTBOX", data_dir)
    sms.send("Referral for K7P-3QZ", number="+23276123456")
    raw = (data_dir / "sms.jsonl").read_bytes()
    assert b"23276123456" not in raw and secure_store.read_jsonl(data_dir / "sms.jsonl")[0]["text"] == "Referral for K7P-3QZ"
    sync.enqueue_bundle("ENC1", {"resourceType": "Bundle", "entry": [{"name": "Mariama"}]})
    f = next((data_dir / "outbox").glob("*.json"))
    assert b"Mariama" not in f.read_bytes() and sync.pending()[0]["code"] == "ENC1"


# ---- audit
def test_audit_refuses_personal_details():
    with pytest.raises(ValueError):
        audit.log("woman-opened", "w", name="Mariama")
    with pytest.raises(ValueError):
        audit.log("not-an-event")


def test_audit_trail_through_the_api(client, data_dir):
    client.post("/api/login", json={"username": "test", "pin": "000000"})
    card = client.post("/api/woman/new", json=REG).json()["woman"]["card_code"]
    client.post("/api/woman/find", json={"card_code": card})
    client.get("/api/woman/record")
    client.post("/api/logout")
    events = [e["event"] for e in audit.read()]
    for ev in ("login", "login-failed", "woman-created", "privacy-notice-given", "woman-opened", "record-shown-to-woman", "logout"):
        assert ev in events, ev
    raw = (data_dir / "audit.jsonl").read_bytes()
    assert b"Mariama" not in raw and b"nurse-test" not in raw  # encrypted


# ---- audio
def test_uploaded_audio_is_deleted_after_transcription(client, monkeypatch, tmp_path):
    seen = {}

    def fake_transcribe(path, lang):
        seen["path"] = Path(path)
        assert seen["path"].exists()
        return server.transcribe.__class__  # never reached

    class R:
        ok, text, model, message = True, "she is bleeding", "fake", ""

    monkeypatch.setattr(server, "transcribe", lambda path, lang: (seen.setdefault("path", Path(path)), R())[1])
    r = client.post("/api/transcribe", files={"audio": ("rec.webm", io.BytesIO(b"fake audio"), "audio/webm")}, data={"lang": "en"})
    assert r.json()["ok"] and not seen["path"].exists()


def test_audio_deleted_even_when_transcription_fails(client, monkeypatch):
    seen = {}

    def boom(path, lang):
        seen["path"] = Path(path)
        raise RuntimeError("decoder crashed")

    monkeypatch.setattr(server, "transcribe", boom)
    with pytest.raises(RuntimeError):
        client.post("/api/transcribe", files={"audio": ("rec.webm", io.BytesIO(b"x"), "audio/webm")}, data={"lang": "en"})
    assert not seen["path"].exists()


def test_read_aloud_of_her_details_leaves_no_audio_on_disk(client, monkeypatch, tmp_path):
    calls = {}

    def fake_speak(text, lang, clip_key=None, cache=True):
        calls["cache"] = cache
        p = tmp_path / "once.wav"
        p.write_bytes(b"RIFF")
        calls["path"] = p
        return p, "fake voice"

    monkeypatch.setattr(server, "speak", fake_speak)
    r = client.post("/api/speak", json={"text": "Card number: K, 7, P, 3, Q, Z", "lang": "en"})
    assert r.status_code == 200 and calls["cache"] is False and not calls["path"].exists()
    client.post("/api/speak", json={"prompt": "privacy_notice", "lang": "en"})
    assert calls["cache"] is True  # shared wording may be cached


def test_training_code_never_reads_app_data():
    """Voice and patient data are never used for training: the training scripts read only public
    datasets (Kaggle notebook) and our own template sentences plus the curated text set."""
    train = (ROOT / "ml/textclf/train.py").read_text() + (ROOT / "ml/textclf/make_training_data.py").read_text()
    assert "registry" not in train and "outbox" not in train and "audit" not in train


# ---- sessions
def test_idle_sign_out(client, monkeypatch):
    assert client.get("/api/state").status_code == 200
    token = client.headers["Authorization"].removeprefix("Bearer ")
    server.TOKENS[token].last_seen -= server.IDLE_SECONDS + 1
    r = client.get("/api/state")
    assert r.status_code == 401 and "without use" in r.json()["detail"]
    assert client.get("/api/state").status_code == 401  # token is gone
    assert "idle-logout" in [e["event"] for e in audit.read()]


def test_sign_in_ends_after_one_shift(client):
    token = client.headers["Authorization"].removeprefix("Bearer ")
    server.TOKENS[token].started -= server.MAX_SESSION_SECONDS + 1
    assert client.get("/api/state").status_code == 401


def test_pin_field_not_remembered_by_browser():
    js = (ROOT / "apps/prototype/web/app.js").read_text()
    assert 'autocomplete="current-password"' not in js


# ---- notice and her record
def test_registration_needs_privacy_notice(client):
    r = client.post("/api/woman/new", json={**REG, "notice_given": False})
    assert r.status_code == 422 and "privacy notice" in r.json()["detail"]


def test_she_can_see_her_record(client):
    client.post("/api/woman/new", json=REG)
    rec = client.get("/api/woman/record").json()
    assert "Mariama" in rec["details"].values() and rec["privacy_notice_at"]


# ---- anonymised export
def test_anonymised_export_drops_identifiers(client):
    client.post("/api/woman/new", json=REG)
    sys.path.insert(0, str(ROOT / "scripts"))
    import export_anonymised
    rows = export_anonymised.rows()
    flat = json.dumps(rows)
    assert rows and "Mariama" not in flat and "23276000000" not in flat
    assert set(rows[0]) >= {"pseudonym", "age_band", "visits"} and "card_code" not in rows[0] and "woman_id" not in rows[0]


# ---- returning woman: her earlier checks are kept and shown
def test_finished_check_is_summarised_in_her_record(client):
    card = client.post("/api/woman/new", json=REG).json()["woman"]["card_code"]
    client.post("/api/extract", json={"transcript": "She has heavy vaginal bleeding since this morning. No fever.", "lang": "en"})
    for f in ("vaginal_bleeding", "bleeding_amount", "fever"):
        client.post("/api/confirm", json={"field": f})
    for f, v in (("systolic", "90"), ("diastolic", "60")):
        client.post("/api/measure", json={"field": f, "value": v}); client.post("/api/confirm", json={"field": f})
    client.post("/api/finish")
    client.post("/api/decision", json={"choice": "planned", "reason": "Ambulance not available; family transport arranged"})
    client.post("/api/woman/find", json={"card_code": card})
    last = client.get("/api/state").json()["woman"]["last_check"]
    assert "Vaginal bleeding" in last["findings"] and "Fever" in last["denied"]
    assert last["measurements"]["Blood pressure"] == "90/60" and last["decision"]
    assert client.get("/api/woman/record").json()["history"][0] == last


def test_demo_women_have_a_previous_check():
    registry.seed_demo()
    w, _ = registry.find("ANC-24T")
    assert w.visits == 1 and len(w.history) == 1 and w.history[0]["measurements"]["Blood pressure"] == "122/78"
