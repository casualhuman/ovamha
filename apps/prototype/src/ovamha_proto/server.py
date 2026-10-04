"""Ovamha prototype server: JSON API + the offline web app (apps/prototype/web).

    python -m ovamha_proto.server            # http://localhost:8000
    python -m ovamha_proto.server --https    # self-signed HTTPS so phone microphones work over Wi-Fi

Everything runs on this machine. No internet is used during an encounter.
"""
from __future__ import annotations

import argparse
import os
import secrets
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.background import BackgroundTask

from . import audit, fhir_client, guideline, questionnaire, registry, sms, sync
from .asr import model_name, transcribe
from .auth import Worker, login
from .confirm import KEYPAD_FIELDS, Session, fmt, label
from .encounter import Encounter
from .detect import detect
from .fhir_bundle import build_bundle, validate
from .handover import handover_text, isbar, letter
from .numbers import parse_bp, parse_number
from .rules import evaluate, questions_to_ask
from .tts import item_text, speak, text_in

WEB = Path(__file__).resolve().parents[2] / "web"
PLAUSIBLE = {"gestational_age_weeks": (4, 45), "systolic": (50, 300), "diastolic": (20, 200),
             "systolic_repeat": (50, 300), "diastolic_repeat": (20, 200), "pulse": (20, 250),
             "temperature": (30, 45), "fetal_heart_rate": (50, 250)}
CHOICE_FIELDS = {"urine_protein": ["negative", "trace", "+", "++", "+++", "unknown"],
                 "severe_pe_symptoms": [True, False, "unknown"]}
SEVERITY_FIELDS = {"abdominal_pain", "breathing_difficulty", "vomiting", "headache"}

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
    woman: registry.Woman | None = None
    started: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)


TOKENS: dict[str, Visit] = {}
# WHO ANC DAK ANC.NFXNREQ.006: sign out after inactivity. A sign-in also ends after one shift.
IDLE_SECONDS = int(os.environ.get("OVAMHA_IDLE_MINUTES", "15")) * 60
MAX_SESSION_SECONDS = int(os.environ.get("OVAMHA_SESSION_HOURS", "8")) * 3600


def visit(authorization: str = Header(default="")) -> Visit:
    token = authorization.removeprefix("Bearer ").strip()
    v = TOKENS.get(token)
    if not v:
        raise HTTPException(401, "Please sign in.")
    now = time.time()
    if now - v.last_seen > IDLE_SECONDS or now - v.started > MAX_SESSION_SECONDS:
        TOKENS.pop(token, None)
        audit.log("idle-logout", v.worker.worker_id)
        minutes = IDLE_SECONDS // 60
        raise HTTPException(401, f"Signed out after {minutes} minutes without use, to protect her information. Please sign in again."
                            if now - v.last_seen > IDLE_SECONDS else "Your sign-in ended after one shift. Please sign in again.")
    v.last_seen = now
    return v


def _new_session(v: Visit) -> None:
    v.session = Session(worker_id=v.worker.worker_id)
    v.transcript, v.notes, v.encounter, v.bundle = "", [], None, None


def _woman_view(w: registry.Woman | None) -> dict | None:
    if not w:
        return None
    return {"card_code": registry.display(w.card_code), "visits": w.visits, "last_visit": w.last_visit, "new": w.visits == 0,
            "id_check": w.national_id, "birth_date": w.birth_date, "birth_date_estimated": w.birth_date_estimated,
            "name": " ".join(x for x in (w.details.get("first_name"), w.details.get("family_name")) if x),
            "profile_done": bool(w.profile), "profile_derived": questionnaire.derived(w.profile) if w.profile else {},
            "last_check": w.history[-1] if w.history else None}


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
        "finished": v.encounter is not None, "woman": _woman_view(v.woman),
        "needs_profile": bool(v.woman and not v.woman.profile),
    }


# ---------------- config ----------------

@app.get("/api/config")
def config():
    """Hosted copies (OVAMHA_HOSTED=1) show a banner explaining the field deployment is offline."""
    import os

    return {"hosted": os.environ.get("OVAMHA_HOSTED") == "1"}


# ---------------- auth ----------------

class LoginIn(BaseModel):
    username: str
    pin: str


@app.post("/api/login")
def do_login(body: LoginIn):
    w, err = login(body.username, body.pin)
    if not w:
        audit.log("login-locked" if err.startswith("Too many") else "login-failed", outcome="failure",
                  username=(body.username or "").strip().lower()[:40])
        raise HTTPException(401, err)
    audit.log("login", w.worker_id)
    token = secrets.token_urlsafe(24)
    v = Visit(worker=w, lang=w.languages[0] if w.languages else "en")
    _new_session(v)
    TOKENS[token] = v
    return {"token": token, "worker": w.__dict__}


@app.post("/api/logout")
def do_logout(authorization: str = Header(default="")):
    v = TOKENS.pop(authorization.removeprefix("Bearer ").strip(), None)
    if v:
        audit.log("logout", v.worker.worker_id)
    return {"ok": True}


# ---------------- encounter ----------------

class LangIn(BaseModel):
    lang: str


@app.post("/api/encounter/new")
def new_encounter(body: LangIn, v: Visit = Depends(visit)):
    _new_session(v)
    v.woman = None
    v.lang = body.lang
    return state(v)


# ---------------- woman (card number) ----------------

class RegisterIn(BaseModel):
    national_id: str  # "nin" | "none"
    consent: bool = False
    notice_given: bool = False  # the privacy notice was read to her (draft DP Bill 2025 s.27(3))
    birth_date: str | None = None  # exact, YYYY-MM-DD
    age_years: int | None = None  # or her estimated age
    details: dict = {}  # ANC.A4 answers (content/questions/anc-registration.json)


@app.post("/api/woman/new")
def woman_new(body: RegisterIn, v: Visit = Depends(visit)):
    """First visit: ID question first, then her woman ID and card number are created (always)."""
    details, problems = questionnaire.validate("anc-registration", body.details)
    if problems:
        raise HTTPException(422, " ".join(problems))
    try:
        v.woman = registry.register(v.worker.worker_id, body.national_id, body.consent, body.birth_date,
                                    body.age_years, details, notice_given=body.notice_given)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    audit.log("woman-created", v.worker.worker_id, woman=v.woman.woman_id)
    audit.log("privacy-notice-given", v.worker.worker_id, woman=v.woman.woman_id)
    return state(v)


QUESTION_SETS = {"anc-registration", "anc-profile"}


@app.get("/api/questions/{name}")
def get_questions(name: str, v: Visit = Depends(visit)):
    if name not in QUESTION_SETS:
        raise HTTPException(404, "Unknown question set.")
    return questionnaire.load(name)


class ProfileIn(BaseModel):
    answers: dict


@app.post("/api/profile")
def save_profile(body: ProfileIn, v: Visit = Depends(visit)):
    """ANC.B6: her history and profile, collected at her first contact (after the quick check)."""
    if not v.woman:
        raise HTTPException(409, "Choose First visit or Returning first.")
    profile, problems = questionnaire.validate("anc-profile", body.answers)
    if problems:
        raise HTTPException(422, " ".join(problems))
    v.woman = registry.save_profile(v.woman.card_code, profile)
    return state(v)


class CardIn(BaseModel):
    card_code: str


@app.post("/api/woman/find")
def woman_find(body: CardIn, v: Visit = Depends(visit)):
    w, err = registry.find(body.card_code)
    if not w:
        raise HTTPException(404, err)
    v.woman = w
    audit.log("woman-opened", v.worker.worker_id, woman=w.woman_id)  # ANC.NFXNREQ.019
    return state(v)


@app.get("/api/woman/record")
def woman_record(v: Visit = Depends(visit)):
    """Show her what this device holds about her (HIS Policy 2021 s.3.5.10(a); draft DP Bill 2025 s.43)."""
    if not v.woman:
        raise HTTPException(409, "Open her card first.")
    audit.log("record-shown-to-woman", v.worker.worker_id, woman=v.woman.woman_id)
    rec = registry.her_record(v.woman)
    for key, qset in (("details", "anc-registration"), ("profile", "anc-profile")):  # readable labels, not codes
        rec[key] = {(questionnaire.find_question(qset, q) or {}).get("label", q): questionnaire.display(qset, q, val)
                    for q, val in rec[key].items()}
    return rec


@app.get("/api/state")
def get_state(v: Visit = Depends(visit)):
    return state(v)


def _transcribe_upload(upload: UploadFile, lang: str):
    """Transcribe a recording, then delete it. Audio is never stored, logged or used for training
    (architecture DEV-03; see docs/privacy/voice-data.md)."""
    suffix = Path(upload.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fh:
        fh.write(upload.file.read())
        path = fh.name
    try:
        return transcribe(path, lang)
    finally:
        Path(path).unlink(missing_ok=True)


@app.post("/api/transcribe")
def do_transcribe(audio: UploadFile = File(...), lang: str = Form("en"), v: Visit = Depends(visit)):
    r = _transcribe_upload(audio, lang)
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
    det = detect(body.transcript, body.lang)
    ex = det.extraction
    v.session.propose_from_extraction(ex, det.field_source)
    v.session.propose_flags(det.flags)
    v.notes.extend(det.notes)
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
    r = _transcribe_upload(audio, lang)
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
    questionnaire: str | None = None
    question: str | None = None
    option: str | None = None
    prompt: str | None = None
    field: str | None = None
    value: str | float | bool | None = None
    text: str | None = None
    lang: str | None = None


@app.post("/api/speak")
def do_speak(body: SpeakIn, v: Visit = Depends(visit)):
    lang = body.lang or v.lang
    if body.questionnaire and body.question:
        q = questionnaire.find_question(body.questionnaire, body.question) if body.questionnaire in QUESTION_SETS else None
        if not q:
            raise HTTPException(404, "Unknown question.")
        text, spoken_lang = questionnaire.say(q, lang, body.option)
    elif body.prompt:
        text, spoken_lang = text_in(lang, body.prompt, body.text or body.prompt)
    elif body.field:
        val = v.session.proposals[body.field].value if body.value is None and body.field in v.session.proposals else body.value
        text, spoken_lang = item_text(body.field, label(body.field), val, lang)
    elif body.text:
        text, spoken_lang = body.text, lang
    else:
        raise HTTPException(422, "Nothing to read.")
    personal = bool(body.text) and not body.prompt  # free text: her transcript, card number, handover
    path, voice = speak(text, spoken_lang, cache=not personal)
    if not path:
        raise HTTPException(503, voice)
    headers = {"X-Ovamha-Voice": voice, "X-Ovamha-Lang": spoken_lang}
    cleanup = BackgroundTask(Path(path).unlink, missing_ok=True) if personal else None  # deleted once sent
    return FileResponse(path, media_type="audio/wav", headers=headers, background=cleanup)


# ---------------- finish, SMS, FHIR ----------------

def _advice_view(e: Encounter) -> dict:
    return {
        "advice": [{"id": a.id, "kind": a.kind, "title": a.title, "kind_title": guideline.KIND_TITLE[a.kind], "reasons": a.reasons,
                    "recommendation": a.recommendation, "cite": a.cite, "source": a.source, "assumptions": a.assumptions}
                   for a in e.advice],
        "suggestion": e.suggestion, "next_contact": e.next_contact,
        "pathway": guideline.guide()["referral_pathway"],
    }


@app.post("/api/finish")
def do_finish(v: Visit = Depends(visit)):
    """Assess: discard unconfirmed items, apply WHO DAK rules and national guideline advice.

    Nothing is referred here. The health worker reads the advice and decides (/api/decision).
    """
    if not v.woman:
        raise HTTPException(409, "Choose First visit or enter her card number first.")
    s = v.session
    confirmed = s.finalise()  # unconfirmed items are discarded here
    results = evaluate(confirmed)
    e = Encounter(confirmed, dict(s.sources), results, v.lang, s.worker_id, v.asr_model or model_name(v.lang))
    e.facility, e.facility_level, e.worker_role = v.worker.facility, v.worker.facility_level, v.worker.role
    e.worker_name = v.worker.display_name
    e.woman_id, e.card_code = v.woman.woman_id, v.woman.card_code
    e.episode_id = v.woman.episode_id or e.episode_id
    e.national_id = v.woman.national_id
    e.birth_date, e.birth_date_estimated = v.woman.birth_date, v.woman.birth_date_estimated
    e.details, e.profile = dict(v.woman.details), dict(v.woman.profile)
    e.profile_derived = questionnaire.derived(v.woman.profile) if v.woman.profile else {}
    e.advice = guideline.advise(confirmed, results, e.profile, e.birth_date, e.facility_level)
    e.suggestion = guideline.top_suggestion(e.advice, results)
    ga = confirmed.get("gestational_age_weeks") or e.profile_derived.get("ga_weeks")
    e.next_contact = guideline.next_contact(ga)
    v.encounter, v.bundle = e, None
    e.management = guideline.management(e.advice, confirmed, ga)
    e.routine = guideline.routine_care(ga, first_contact=v.woman.visits == 0)
    view = {**_rule_view(results), **_advice_view(e), "management": e.management, "routine": e.routine,
            "code": e.code, "card_code": registry.display(e.card_code)}
    # Translated copies (e.g. Yoruba), shown with the English one tap away; the English stays the record.
    view["translations"] = {l: t for l in ("yo", "kri") if (t := guideline.localise(view, l))}
    view["lang"] = v.lang
    return view


class DecisionIn(BaseModel):
    choice: str  # "urgent" | "planned" | "none"
    reason: str | None = None


@app.post("/api/decision")
def do_decision(body: DecisionIn, v: Visit = Depends(visit)):
    """The health worker's decision. Ovamha suggested; the worker decides and is recorded as deciding."""
    e = v.encounter
    if not e:
        raise HTTPException(409, "Assess the woman first.")
    if body.choice not in ("urgent", "planned", "none"):
        raise HTTPException(422, "Choose urgent referral, planned referral or no referral.")
    reason = (body.reason or "").strip()
    if e.suggestion != "none" and body.choice == "none" and not reason:
        raise HTTPException(422, "The guideline suggests referral. Record your reason for not referring now.")
    if e.suggestion == "urgent_referral" and body.choice == "planned" and not reason:
        raise HTTPException(422, "The guideline suggests urgent referral. Record your reason for a planned referral instead.")
    e.decision = {"choice": body.choice, "reason": reason or None, "at": _now(), "by": v.worker.worker_id, "suggested": e.suggestion}
    if body.choice == "urgent":
        return {"next": "referral", "isbar": isbar(e), **_advice_view(e)}
    return {"next": "done", **_complete(v)}


class ReferralIn(BaseModel):
    consent: bool
    checklist: list[int] = []
    call_time: str | None = None
    ambulance_time: str | None = None


@app.post("/api/referral/complete")
def referral_complete(body: ReferralIn, v: Visit = Depends(visit)):
    """Urgent referral pathway (national guideline): consent, pre-referral checklist, iSBAR call, then notify."""
    e = v.encounter
    if not e or not e.decision or e.decision["choice"] != "urgent":
        raise HTTPException(409, "Decide on urgent referral first.")
    items = guideline.guide()["referral_pathway"]["emergency_checklist"]
    e.referral_steps = {"consent": body.consent, "checklist": [items[i] for i in body.checklist if 0 <= i < len(items)],
                        "call_time": body.call_time, "ambulance_time": body.ambulance_time}
    if not body.consent:
        e.decision["reason"] = (e.decision.get("reason") or "") + " The woman did not consent to referral."
    return _complete(v)


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


SUGGESTION_TEXT = {"urgent_referral": "Urgent referral suggested", "refer_cemonc": "Referral to a CEmONC facility suggested",
                   "refer_assessment": "Referral for assessment suggested",
                   "plan_cemonc_delivery": "Plan delivery at a CEmONC facility", "none": "No referral suggested"}
DECISION_LABEL = {"urgent": "Urgent referral", "planned": "Planned referral (not an emergency)", "none": "No referral at this contact"}


def visit_summary(e: Encounter) -> dict:
    """What a later check needs to know about this one: confirmed findings, measurements, advice, decision."""
    c = e.confirmed
    yes = [label(f) + (f" ({c[f]})" if c[f] in ("severe", "mild") else "") for f in c
           if f not in KEYPAD_FIELDS and f != "bleeding_amount" and c[f] not in (False, None, "unknown", "negative")
           and f not in ("urine_protein", "severe_pe_symptoms")]
    if c.get("bleeding_amount") not in (None, "not captured"):
        yes.append(f"Bleeding amount: {c['bleeding_amount']}")
    meas = {}
    if c.get("systolic") and c.get("diastolic"):
        meas["Blood pressure"] = f"{c['systolic']}/{c['diastolic']}"
    for f in ("systolic_repeat", "pulse", "temperature", "fetal_heart_rate", "urine_protein"):
        if c.get(f) not in (None, "unknown"):
            meas[label(f)] = str(c[f])
    ga = c.get("gestational_age_weeks") or e.profile_derived.get("ga_weeks")
    d = e.decision or {}
    return {"at": e.at, "ga_weeks": round(float(ga)) if ga else None, "worker": e.worker_name or e.worker_id,
            "facility": e.facility, "findings": yes,
            "denied": [label(f) for f in c if c[f] is False and f not in KEYPAD_FIELDS],
            "measurements": meas, "guideline": SUGGESTION_TEXT.get(e.suggestion, e.suggestion),
            "decision": DECISION_LABEL.get(d.get("choice"), d.get("choice") or ""), "reason": d.get("reason") or "",
            "referral_code": e.code if e.referral else None}


def _complete(v: Visit) -> dict:
    """Record the encounter: notify the receiving facility for an urgent referral, build the FHIR record, queue sync."""
    e = v.encounter
    registry.record_visit(e.card_code, visit_summary(e))
    audit.log("encounter-finished", v.worker.worker_id, woman=e.woman_id, encounter=e.code)
    out_sms = None
    if e.urgent and not e.sms:
        m = sms.send(sms.referral_text(e))
        audit.log("sms-sent", v.worker.worker_id, encounter=e.code, channel=m.channel)
        out_sms = {"text": m.text, "channel": m.channel, "at": m.at}
        e.sms = {"text": m.text, "sent": m.at, "channel": m.channel}
    out_reminder = None
    if not e.urgent and sms.wants_reminder(e) and not e.reminder:
        text = sms.reminder_text(e)
        if text:
            m = sms.send(text, e.details["phone"], kind="reminder")
            audit.log("sms-reminder-sent", v.worker.worker_id, encounter=e.code, channel=m.channel)
            out_reminder = e.reminder = {"text": m.text, "channel": m.channel, "at": m.at, "to": m.number}
    v.bundle = build_bundle(e)
    try:
        validate(v.bundle)
        valid = {"ok": True, "message": "FHIR Bundle passes structural validation (fhir.resources, R4B models)."}
        sync.enqueue_bundle(e.code, v.bundle)  # SY-01: saved on the device; uploads itself when the hub is reachable
    except Exception as exc:  # show, never hide, a validation failure; an invalid Bundle is never queued
        valid = {"ok": False, "message": str(exc)}
    return {"decision": e.decision, "referral": e.referral, "urgent": e.urgent, "code": e.code,
            "card_code": registry.display(e.card_code), "sync": sync.status(e.code), "handover": handover_text(e),
            "isbar": isbar(e), "letter": letter(e) if e.referral else None, "sms": out_sms, "reminder": out_reminder, "status": e.referral_status, "bundle": v.bundle, "valid": valid,
            "next_contact": e.next_contact}


@app.get("/api/sms/log")
def sms_log(v: Visit = Depends(visit)):
    """Messages sent and received (the demo phone shows them as they arrive)."""
    return {"messages": sms.log(), "hospital": sms.REFERRAL_NUMBER}


class ReplyIn(BaseModel):
    text: str


@app.post("/api/sms/reply")
def do_reply(body: ReplyIn, v: Visit = Depends(visit)):
    e = v.encounter
    if not e:
        raise HTTPException(409, "Finish the encounter first.")
    status = sms.handle_reply(body.text, e)
    audit.log("sms-received", v.worker.worker_id, encounter=e.code, matched=status is not None)
    if status:
        sync.enqueue_task_status(e.code, status)  # Task -> accepted / rejected on the hub, via the outbox
    return {"status": e.referral_status, "matched": status is not None, "sync": sync.status(e.code)}


@app.get("/api/sync")
def sync_status(v: Visit = Depends(visit)):
    """Where this encounter's record is: saved on the device, waiting, or synced to the hub."""
    return sync.status(v.encounter.code if v.encounter else None)


@app.post("/api/sync/now")
def sync_now(v: Visit = Depends(visit)):
    """Try the hub now instead of waiting for the next background attempt."""
    sync.flush()
    return sync.status(v.encounter.code if v.encounter else None)


# ---------------- static web app ----------------

@app.get("/")
def index():
    return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-cache"})


@app.middleware("http")
async def _no_stale_assets(request, call_next):
    """Browsers revalidate the app's files on every load, so an update is never hidden by a cached copy."""
    response = await call_next(request)
    if not request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/", StaticFiles(directory=WEB), name="web")


@app.on_event("startup")
def _start_sync() -> None:
    from .tts import CACHE
    for f in CACHE.glob("once-*.wav"):  # one-off read-aloud audio left by an interrupted request
        f.unlink(missing_ok=True)
    registry.seed_demo()  # fictional returning woman MAM-A2A, for testing a returning check
    sync.start_worker()


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
