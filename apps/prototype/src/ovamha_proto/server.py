"""Ovamha prototype server: JSON API + the offline web app (apps/prototype/web).

    python -m ovamha_proto.server            # http://localhost:8000
    python -m ovamha_proto.server --https    # self-signed HTTPS so phone microphones work over Wi-Fi

Everything runs on this machine. No internet is used during an encounter.
"""
from __future__ import annotations

import argparse
import secrets
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import fhir_client, sms
from .asr import model_name, transcribe
from .auth import Worker, login, workers
from .confirm import KEYPAD_FIELDS, Session, fmt, label
from .encounter import Encounter
from .extract import extract
from .fhir_bundle import build_bundle, validate
from .handover import handover_text
from .numbers import parse_bp, parse_number
from .rules import evaluate, questions_to_ask
from .safety_net import scan
from .tts import item_text, speak

WEB = Path(__file__).resolve().parents[2] / "web"
PLAUSIBLE = {"gestational_age_weeks": (4, 45), "systolic": (50, 300), "diastolic": (20, 200),
             "systolic_repeat": (50, 300), "diastolic_repeat": (20, 200), "pulse": (20, 250),
             "temperature": (30, 45), "fetal_heart_rate": (50, 250)}
CHOICE_FIELDS = {"urine_protein": ["negative", "trace", "+", "++", "+++", "unknown"],
                 "severe_pe_symptoms": [True, False, "unknown"]}
SEVERITY_FIELDS = {"abdominal_pain", "breathing_difficulty", "vomiting"}

app = FastAPI(title="Ovamha prototype", docs_url=None, redoc_url=None)


@dataclass
class Visit:
    worker: Worker
    lang: str = "en"
    session: Session = field(default_factory=Session)
    transcript: str = ""
    asr_model: str = ""
    notes: list[str] = field(default_factory=list)
    encounter: Encounter | None = None
    bundle: dict | None = None
    fhir_ids: dict = field(default_factory=dict)


TOKENS: dict[str, Visit] = {}


def visit(authorization: str = Header(default="")) -> Visit:
    v = TOKENS.get(authorization.removeprefix("Bearer ").strip())
    if not v:
        raise HTTPException(401, "Please sign in.")
    return v


def _new_session(v: Visit) -> None:
    v.session = Session(worker_id=v.worker.worker_id)
    v.transcript, v.notes, v.encounter, v.bundle, v.fhir_ids = "", [], None, None, {}


def _rule_view(results) -> dict:
    danger = any(r.rule_id == "ANC.DT.01" and r.fired for r in results)
    return {
        "danger": danger,
        "referral": any(r.fired for r in results),
        "ask_next": [{"field": f, "label": label(f)} for f in questions_to_ask(results)],
        "rules": [{
            "id": r.rule_id, "name": r.name,
            "status": "deferred" if danger and r.status == "needs_data" else r.status,
            "reasons": r.reasons, "actions": r.actions, "notes": r.notes, "source": r.source, "label": r.label,
        } for r in results],
    }


def state(v: Visit) -> dict:
    s = v.session
    items = []
    for f, p in s.proposals.items():
        items.append({
            "field": f, "label": label(f), "value": p.value, "display": fmt(p.value), "source": p.source,
            "evidence": p.evidence, "confirmed": f in s.confirmed,
            "confirmed_value": fmt(s.confirmed[f]) if f in s.confirmed else None,
            "kind": "number" if f in KEYPAD_FIELDS else "severity" if f in SEVERITY_FIELDS else "choice",
        })
    return {
        "worker": v.worker.__dict__, "lang": v.lang, "transcript": v.transcript, "notes": v.notes,
        "items": items, "preview": _rule_view(evaluate(s.confirmed)) if s.confirmed else None,
        "finished": v.encounter is not None,
    }


# ---------------- auth ----------------

class LoginIn(BaseModel):
    worker_id: str
    pin: str


@app.get("/api/workers")
def list_workers():
    return [{"worker_id": w.worker_id, "display_name": w.display_name, "role": w.role} for w in workers()]


@app.post("/api/login")
def do_login(body: LoginIn):
    w, err = login(body.worker_id, body.pin)
    if not w:
        raise HTTPException(401, err)
    token = secrets.token_urlsafe(24)
    v = Visit(worker=w, lang=w.languages[0] if w.languages else "en")
    _new_session(v)
    TOKENS[token] = v
    return {"token": token, "worker": w.__dict__}


@app.post("/api/logout")
def do_logout(authorization: str = Header(default="")):
    TOKENS.pop(authorization.removeprefix("Bearer ").strip(), None)
    return {"ok": True}


# ---------------- encounter ----------------

class LangIn(BaseModel):
    lang: str


@app.post("/api/encounter/new")
def new_encounter(body: LangIn, v: Visit = Depends(visit)):
    _new_session(v)
    v.lang = body.lang
    return state(v)


@app.get("/api/state")
def get_state(v: Visit = Depends(visit)):
    return state(v)


def _save_upload(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fh:
        fh.write(upload.file.read())
        return fh.name


@app.post("/api/transcribe")
def do_transcribe(audio: UploadFile = File(...), lang: str = Form("en"), v: Visit = Depends(visit)):
    r = transcribe(_save_upload(audio), lang)
    if not r.ok:
        return JSONResponse({"ok": False, "message": r.message}, status_code=422)
    v.asr_model = r.model
    return {"ok": True, "text": r.text, "model": r.model, "note": r.message}


class ExtractIn(BaseModel):
    transcript: str
    lang: str


@app.post("/api/extract")
def do_extract(body: ExtractIn, v: Visit = Depends(visit)):
    if not body.transcript.strip():
        raise HTTPException(422, "Nothing to read back yet.")
    _new_session(v)
    v.lang, v.transcript = body.lang, body.transcript
    v.asr_model = v.asr_model or model_name(body.lang)
    ex = extract(body.transcript, body.lang)
    v.session.propose_from_extraction(ex)
    flags = scan(ex)
    v.session.propose_flags(flags)
    ga = ex.fields["gestational_age_weeks"]
    if ga.captured:
        v.notes.append(f"Heard {ga.value} weeks. Enter gestational age in Measurements to confirm it.")
    return state(v)


class ConfirmIn(BaseModel):
    field: str
    value: str | float | bool | None = None


def _coerce(f: str, value):
    if isinstance(value, str):
        low = value.strip().lower()
        if low in ("yes", "true"):
            return True
        if low in ("no", "false"):
            return False
        return value.strip()
    return value


@app.post("/api/confirm")
def do_confirm(body: ConfirmIn, v: Visit = Depends(visit)):
    if body.field not in v.session.proposals:
        raise HTTPException(404, "Item not found.")
    v.session.confirm(body.field, None if body.value is None else _coerce(body.field, body.value))
    return state(v)


class FieldIn(BaseModel):
    field: str


@app.post("/api/reject")
def do_reject(body: FieldIn, v: Visit = Depends(visit)):
    v.session.reject(body.field)
    return state(v)


@app.post("/api/unconfirm")
def do_unconfirm(body: FieldIn, v: Visit = Depends(visit)):
    v.session.confirmed.pop(body.field, None)
    v.session.sources.pop(body.field, None)
    return state(v)


class MeasureIn(BaseModel):
    field: str
    value: str | float | bool


@app.post("/api/measure")
def do_measure(body: MeasureIn, v: Visit = Depends(visit)):
    """Propose a measurement (typed or from voice). It still needs a confirm."""
    f, val = body.field, body.value
    if f in PLAUSIBLE:
        try:
            num = float(val)
        except (TypeError, ValueError):
            raise HTTPException(422, f"{label(f)}: enter a number.")
        lo, hi = PLAUSIBLE[f]
        if not lo <= num <= hi:
            raise HTTPException(422, f"{label(f)} {val} looks wrong (expected {lo}-{hi}). Please re-enter.")
        val = int(num) if num.is_integer() else num
    elif f in CHOICE_FIELDS:
        val = _coerce(f, val) if isinstance(val, str) else val
        if val not in CHOICE_FIELDS[f]:
            raise HTTPException(422, "Choose one of the options.")
    else:
        raise HTTPException(404, "Unknown measurement.")
    v.session.propose_keypad(f, val)
    return state(v)


@app.post("/api/number-voice")
def number_voice(audio: UploadFile = File(...), field: str = Form(...), lang: str = Form("en"), v: Visit = Depends(visit)):
    """Transcribe a spoken number. Returns the value to put in the field; nothing is proposed or confirmed."""
    r = transcribe(_save_upload(audio), lang)
    if not r.ok:
        return JSONResponse({"ok": False, "message": r.message}, status_code=422)
    if field in ("systolic", "diastolic", "systolic_repeat", "diastolic_repeat"):
        bp = parse_bp(r.text)
        if bp:
            suffix = "_repeat" if field.endswith("_repeat") else ""
            return {"ok": True, "heard": r.text, "values": {f"systolic{suffix}": bp[0], f"diastolic{suffix}": bp[1]}}
    n = parse_number(r.text)
    if n is None:
        return JSONResponse({"ok": False, "heard": r.text, "message": f"Heard “{r.text}”. Please say just the number, or type it."}, status_code=422)
    return {"ok": True, "heard": r.text, "values": {field: n}}


# ---------------- read aloud ----------------

class SpeakIn(BaseModel):
    field: str | None = None
    value: str | float | bool | None = None
    text: str | None = None
    lang: str | None = None


@app.post("/api/speak")
def do_speak(body: SpeakIn, v: Visit = Depends(visit)):
    lang = body.lang or v.lang
    if body.field:
        val = v.session.proposals[body.field].value if body.value is None and body.field in v.session.proposals else body.value
        text, spoken_lang = item_text(body.field, label(body.field), val, lang)
    elif body.text:
        text, spoken_lang = body.text, lang
    else:
        raise HTTPException(422, "Nothing to read.")
    path, voice = speak(text, spoken_lang)
    if not path:
        raise HTTPException(503, voice)
    headers = {"X-Ovamha-Voice": voice, "X-Ovamha-Lang": spoken_lang}
    return FileResponse(path, media_type="audio/wav", headers=headers)


# ---------------- finish, SMS, FHIR ----------------

@app.post("/api/finish")
def do_finish(v: Visit = Depends(visit)):
    s = v.session
    confirmed = s.finalise()  # unconfirmed items are discarded here
    results = evaluate(confirmed)
    e = Encounter(confirmed, dict(s.sources), results, v.lang, s.worker_id, v.asr_model or model_name(v.lang))
    e.facility = v.worker.facility
    v.encounter = e
    v.bundle = build_bundle(e)
    try:
        validate(v.bundle)
        valid = {"ok": True, "message": "FHIR Bundle passes structural validation (fhir.resources, R4B models)."}
    except Exception as exc:  # show, never hide, a validation failure
        valid = {"ok": False, "message": str(exc)}
    out_sms = None
    if e.referral:
        m = sms.send(sms.referral_text(e))
        out_sms = {"text": m.text, "channel": m.channel, "at": m.at}
    return {**_rule_view(results), "code": e.code, "handover": handover_text(e), "sms": out_sms,
            "status": e.referral_status, "bundle": v.bundle, "valid": valid}


class ReplyIn(BaseModel):
    text: str


@app.post("/api/sms/reply")
def do_reply(body: ReplyIn, v: Visit = Depends(visit)):
    e = v.encounter
    if not e:
        raise HTTPException(409, "Finish the encounter first.")
    status = sms.handle_reply(body.text, e)
    out = {"status": e.referral_status, "matched": status is not None, "fhir": None}
    task = v.fhir_ids.get("Task")
    if status and task and fhir_client.available():
        out["fhir"] = {"task": task, "status": fhir_client.set_task_status(task, status).get("status")}
    return out


@app.post("/api/fhir/post")
def post_fhir(v: Visit = Depends(visit)):
    if not v.bundle:
        raise HTTPException(409, "Finish the encounter first.")
    if not fhir_client.available():
        raise HTTPException(503, f"FHIR server not reachable at {fhir_client.FHIR_BASE}. Start it with Docker (hub/docker-compose.yml).")
    v.fhir_ids = fhir_client.server_ids(fhir_client.post_transaction(v.bundle))
    return {"base": fhir_client.FHIR_BASE, "ids": v.fhir_ids}


# ---------------- static web app ----------------

@app.get("/")
def index():
    return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=WEB), name="web")


def _self_signed_cert() -> tuple[str, str]:
    d = Path.home() / ".ovamha"
    d.mkdir(exist_ok=True)
    key, crt = d / "key.pem", d / "cert.pem"
    if not crt.exists():
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30", "-subj", "/CN=ovamha.local",
                        "-keyout", str(key), "-out", str(crt)], check=True, capture_output=True)
    return str(key), str(crt)


def main() -> None:
    import uvicorn

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--https", action="store_true")
    a = ap.parse_args()
    kw = {}
    if a.https:
        key, crt = _self_signed_cert()
        kw = {"ssl_keyfile": key, "ssl_certfile": crt}
    uvicorn.run(app, host="0.0.0.0", port=a.port, **kw)


if __name__ == "__main__":
    main()
