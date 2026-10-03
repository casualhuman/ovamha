"""Ovamha prototype UI (Gradio). Runs offline on a laptop or Raspberry Pi; a phone opens it over local Wi-Fi.

    python -m ovamha_proto.app            # http://<laptop-ip>:7860 (upload audio from phone)
    python -m ovamha_proto.app --https    # self-signed HTTPS so the phone microphone works
"""
from __future__ import annotations

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")  # offline: no telemetry calls

import argparse
import json
import subprocess
from pathlib import Path

import gradio as gr

from . import fhir_client, sms
from .asr import model_name, transcribe
from .auth import Worker, login, workers
from .confirm import Session, fmt, label
from .encounter import Encounter
from .extract import extract
from .fhir_bundle import build_bundle, validate
from .handover import handover_text
from .lexicon import LANGUAGES
from .rules import evaluate, questions_to_ask
from .safety_net import scan

LANG_CHOICES = [(name, code) for code, name in LANGUAGES.items()]
SOURCE_BADGE = {"voice-ai-extracted": "🎙 voice (AI)", "ai-safety-net": "⚠️ AI safety net", "keypad": "⌨️ keypad"}
SIMULATED = "**SIMULATED**"
# Keypad plausibility ranges: values outside are rejected and must be re-entered (0 is never "empty").
PLAUSIBLE = {"gestational_age_weeks": (4, 45), "systolic": (50, 300), "diastolic": (20, 200),
             "systolic_repeat": (50, 300), "diastolic_repeat": (20, 200), "pulse": (20, 250),
             "temperature": (30, 45), "fetal_heart_rate": (50, 250)}


def new_state(worker: Worker | None = None) -> dict:
    session = Session(worker_id=worker.worker_id) if worker else Session()
    return {"session": session, "lang": "en", "asr_model": model_name("en"), "encounter": None, "fhir": {}, "worker": worker}


# ---------------- helpers ----------------

def pending_choices(s: Session):
    return [(f"{lab}: {val}  ·  {SOURCE_BADGE.get(src, src)}", f) for f, lab, val, src in s.readback()]


def readback_md(s: Session) -> str:
    rows = [(f, p) for f, p in s.proposals.items() if f not in s.confirmed]
    if not rows:
        return "_Nothing waiting for confirmation._"
    out = ["| Item | Proposed | Source | Heard as |", "|---|---|---|---|"]
    for f, p in rows:
        out.append(f"| {label(f)} | **{fmt(p.value)}** | {SOURCE_BADGE.get(p.source, p.source)} | {p.evidence or '-'} |")
    return "\n".join(out)


def confirmed_md(s: Session) -> str:
    if not s.confirmed:
        return "_Nothing confirmed yet. Only confirmed items count._"
    return "\n".join(f"- ✅ {label(f)}: **{fmt(v)}** ({s.sources.get(f, '')})" for f, v in s.confirmed.items())


def rules_md(results, final: bool) -> str:
    out = []
    danger = any(r.rule_id == "ANC.DT.01" and r.fired for r in results)
    for r in results:
        if danger and r.status == "needs_data":
            out.append(f"### ⏸ {r.rule_id} {r.name}: DEFERRED (danger sign: refer first, no history questions)")
            continue
        icon = {"fired": "🔴", "not_fired": "🟢", "needs_data": "🟡"}[r.status]
        out.append(f"### {icon} {r.rule_id} {r.name}: {r.status.replace('_', ' ').upper()}")
        if r.reasons:
            out.append("Because: " + "; ".join(r.reasons))
        out += [f"- **{a}**" for a in r.actions]
        out += [f"- ⚠️ {n}" for n in r.notes]
        out.append(f"<sub>{r.source}. _{r.label}._</sub>")
    q = questions_to_ask(results)
    if danger:
        out.append("\n**Danger sign present: refer now. No further history questions.**")
    elif q:
        out.append("\n**Ask next (unknown is never normal):** " + ", ".join(label(x) for x in q))
    if not final:
        out.append("\n_Preview on confirmed items so far. Press **Finish encounter** to discard unconfirmed items and send._")
    return "\n\n".join(out)


def views(st):
    s = st["session"]
    return (
        readback_md(s),
        gr.update(choices=pending_choices(s), value=[]),
        gr.update(choices=[(label(f), f) for f in s.proposals], value=None),
        confirmed_md(s),
        rules_md(evaluate(s.confirmed), final=False) if s.confirmed else "",
    )


# ---------------- actions ----------------

def do_transcribe(audio_path, lang, st):
    st = st or new_state()
    if not audio_path:
        return gr.update(), "Record or upload audio first (or type the description).", st
    r = transcribe(audio_path, lang)
    st["asr_model"] = r.model
    if not r.ok:
        return gr.update(), f"🔁 {r.message}", st
    return r.text, f"Transcribed offline with {r.model}. {r.message}", st


def do_extract(audio_path, transcript, lang, st):
    """Read back for confirmation. Transcribes first if there is audio but no transcript."""
    st = st or new_state()
    asr_note = gr.update()
    if not (transcript or "").strip():
        if not audio_path:
            return (*views(st), "", gr.update(), "⚠️ Record or upload a description, or type it, first.", gr.Tabs(), st)
        r = transcribe(audio_path, lang)
        if not r.ok:
            return (*views(st), "", gr.update(), f"🔁 {r.message}", gr.Tabs(), st)
        transcript, st["asr_model"] = r.text, r.model
        asr_note = f"Transcribed offline with {r.model}. {r.message}"
    st = new_state(st.get("worker")) | {"asr_model": st.get("asr_model", model_name(lang))}
    st["lang"] = lang
    ex = extract(transcript, lang)
    s = st["session"]
    s.propose_from_extraction(ex)
    flags = scan(ex)
    s.propose_flags(flags)
    flagged = {fl.field for fl in flags}
    missing = [label(f) for f, fv in ex.fields.items() if not fv.captured and f != "bleeding_amount" and f not in flagged]
    ga = ex.fields["gestational_age_weeks"]
    notes = []
    if ga.captured:
        notes.append(f"Heard gestational age **{ga.value} weeks**: enter it on the keypad to confirm.")
    if flags:
        notes.append("⚠️ AI safety net raised: " + ", ".join(f"**{f.label}** ({f.reason})" for f in flags))
    notes.append("Not captured (asked only if a rule needs it): " + (", ".join(missing) or "none"))
    return (*views(st), "\n\n".join(notes), transcript, asr_note, gr.Tabs(selected="confirm"), st)


def do_confirm(ticked, st):
    s = st["session"]
    for f in ticked or []:
        s.confirm(f)
    return (*views(st), st)


def do_correct(field, value, st):
    s = st["session"]
    if field and value not in (None, ""):
        v = {"yes": True, "no": False}.get(str(value).strip().lower(), str(value).strip())
        if field in s.proposals:
            s.confirm(field, v)
    return (*views(st), st)


def do_reject(field, st):
    if field:
        st["session"].reject(field)
    return (*views(st), st)


def do_keypad(ga, sys_, dia, rsys, rdia, pulse, temp, fhr, protein, severe, st):
    s = st["session"]
    nums = {"gestational_age_weeks": ga, "systolic": sys_, "diastolic": dia, "systolic_repeat": rsys,
            "diastolic_repeat": rdia, "pulse": pulse, "temperature": temp, "fetal_heart_rate": fhr}
    rejected = []
    for f, v in nums.items():
        if v is None or v == "":
            continue
        lo, hi = PLAUSIBLE[f]
        if not lo <= float(v) <= hi:
            rejected.append(f"{label(f)} {v} (expected {lo}-{hi})")
            continue
        s.propose_keypad(f, int(v) if float(v).is_integer() else float(v))
    if protein:
        s.propose_keypad("urine_protein", protein)
    if severe:
        s.propose_keypad("severe_pe_symptoms", {"Yes": True, "No": False}.get(severe, "unknown"))
    note = ("❌ Not added, please re-enter: " + "; ".join(rejected)) if rejected else ""
    return (*views(st), note, st)


def do_readback_audio(st):
    from .tts import readback_audio

    items = [(f, lab, val) for f, lab, val, _ in st["session"].readback()]
    if not items:
        return None, "Nothing to read back."
    path, note = readback_audio(items, st["lang"])
    return path, note


def do_finish(st):
    s = st["session"]
    confirmed = s.finalise()  # unconfirmed proposals are discarded here
    results = evaluate(confirmed)
    w = st.get("worker")
    e = Encounter(confirmed, dict(s.sources), results, st["lang"], s.worker_id, st["asr_model"])
    if w:
        e.facility = w.facility
    st["encounter"] = e
    bundle = build_bundle(e)
    try:
        validate(bundle)
        valid = "✅ FHIR Bundle passes structural validation (fhir.resources, R4B models)."
    except Exception as exc:  # show, never hide, a validation failure
        valid = f"❌ FHIR validation error: {exc}"
    st["fhir"] = {"bundle": bundle}
    sms_md = "_No referral rule fired: no SMS sent._"
    if e.referral:
        msg = sms.send(sms.referral_text(e))
        tag = SIMULATED if msg.channel == "SIMULATED" else "GSM modem"
        sms_md = f"📤 {tag} SMS to referral facility:\n\n```\n{msg.text}\n```\nReferral status: **{e.referral_status}**"
    return (rules_md(results, final=True), handover_text(e), sms_md, json.dumps(bundle, indent=2), valid, *views(st), st)


def do_post_fhir(st):
    e = st.get("encounter")
    if not e:
        return "Finish the encounter first.", st
    if not fhir_client.available():
        return f"FHIR server not reachable at {fhir_client.FHIR_BASE}. Start it with `make hapi` (needs Docker).", st
    resp = fhir_client.post_transaction(st["fhir"]["bundle"])
    ids = fhir_client.server_ids(resp)
    st["fhir"]["ids"] = ids
    lines = [f"- {t}: `{fhir_client.FHIR_BASE}/{ref}`" for t, ref in ids.items()]
    pat = ids.get("Patient")
    if pat:
        lines.append(f"- Everything for this woman: `{fhir_client.FHIR_BASE}/{pat}/$everything`")
    return "✅ Transaction accepted by HAPI FHIR:\n" + "\n".join(lines), st


def do_reply(text, st):
    e = st.get("encounter")
    if not e:
        return "Finish the encounter first.", st
    status = sms.handle_reply(text or "", e)
    if status is None:
        return f"📥 {SIMULATED} reply `{text}` ignored: not ACK/FULL for encounter {e.code}.", st
    out = f"📥 {SIMULATED} reply `{text}` → referral Task status **{status}**."
    task = st.get("fhir", {}).get("ids", {}).get("Task")
    if task and fhir_client.available():
        t = fhir_client.set_task_status(task, status)
        out += f"\n\nFHIR server: `{task}` status is now **{t.get('status')}** (PUT)."
    return out, st


# ---------------- login ----------------

def do_login(worker_id, pin, st):
    w, err = login(worker_id, pin)
    if not w:
        return gr.update(visible=True), gr.update(visible=False), f"❌ {err}", "", gr.update(value=""), gr.update(), st
    header = f"Signed in as **{w.display_name}** · {w.role} · {w.facility}"
    return (gr.update(visible=False), gr.update(visible=True), "", header, gr.update(value=""),
            gr.update(value=w.languages[0] if w.languages else "en"), new_state(w))


def do_logout(st):
    return gr.update(visible=True), gr.update(visible=False), "", "", gr.update(value=""), gr.update(), new_state()


# ---------------- layout ----------------

SL_BLUE = "#0072C6"  # Sierra Leone flag blue
BLUE = gr.themes.Color(
    c50="#E6F1FA", c100="#CCE3F4", c200="#99C7E9", c300="#66AADD", c400="#338ED2",
    c500="#0072C6", c600="#005EA3", c700="#004A80", c800="#00365E", c900="#00223B", c950="#001629",
    name="sl_blue",
)
THEME = gr.themes.Soft(
    primary_hue=BLUE, secondary_hue=BLUE, neutral_hue="slate",
    font=["system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],  # system fonts: no download, works offline
    text_size=gr.themes.sizes.text_lg, spacing_size=gr.themes.sizes.spacing_lg, radius_size=gr.themes.sizes.radius_lg,
)
CSS = f"""
.gradio-container {{ max-width: 1100px !important; margin: 0 auto !important; font-size: 18px; }}
button {{ font-size: 1.15rem !important; min-height: 56px; }}
input, textarea, select {{ font-size: 1.2rem !important; }}
.tab-wrapper button, [role="tab"] {{ font-size: 1.15rem !important; min-height: 52px; }}
.ov-hero {{ text-align: center; padding: 28px 8px 8px; }}
.ov-hero h1 {{ font-size: 2.8rem; color: {SL_BLUE}; margin: 0; letter-spacing: -0.02em; }}
.ov-hero .sub {{ font-size: 1.35rem; color: var(--body-text-color-subdued); margin-top: 6px; }}
.ov-steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 20px 0 8px; }}
.ov-step {{ border: 1px solid var(--border-color-primary); border-top: 6px solid {SL_BLUE}; border-radius: 14px; padding: 16px 18px; background: var(--block-background-fill); }}
.ov-step b {{ display: block; font-size: 1.25rem; color: {SL_BLUE}; margin-bottom: 4px; }}
.ov-step span {{ font-size: 1.05rem; line-height: 1.45; }}
.ov-safe {{ border-left: 6px solid {SL_BLUE}; background: var(--color-accent-soft); padding: 14px 18px; border-radius: 10px; font-size: 1.1rem; line-height: 1.5; }}
.ov-bar {{ background: {SL_BLUE}; color: white; border-radius: 12px; padding: 12px 18px; }}
.ov-bar p, .ov-bar strong {{ color: white !important; font-size: 1.1rem; margin: 0; }}
"""

HERO = f"""
<div class="ov-hero">
  <h1>Ovamha</h1>
  <div class="sub">Offline voice assistant for maternal care</div>
</div>
<div class="ov-steps">
  <div class="ov-step"><b>1 · Speak</b><span>Describe the pregnant woman's situation in Krio, Yoruba or English.</span></div>
  <div class="ov-step"><b>2 · Confirm</b><span>Ovamha reads back what it heard. You confirm or correct each item. Numbers such as blood pressure are typed, never guessed.</span></div>
  <div class="ov-step"><b>3 · Refer</b><span>It checks WHO danger signs, prepares the handover for the hospital and sends the referral SMS.</span></div>
</div>
<div class="ov-safe">
  <strong>You stay in charge.</strong> Nothing is used until you confirm it. Referral decisions follow WHO antenatal guidance;
  the AI can only add warnings for you to check, it can never remove one. Everything works with no internet.
</div>
"""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Ovamha") as ui:
        st = gr.State(new_state())

        # ----- welcome + sign in (offline) -----
        with gr.Column(visible=True) as login_col:
            gr.HTML(HERO)
            with gr.Group():
                gr.Markdown("## Sign in")
                who = gr.Dropdown([(f"{w.display_name}  ({w.role})", w.worker_id) for w in workers()],
                                  value=None, label="Your name")
                pin = gr.Textbox(label="PIN", type="password", max_lines=1)
                btn_login = gr.Button("Sign in", variant="primary", size="lg")
                login_msg = gr.Markdown()
            gr.Markdown("<sub>Sign-in is checked on this device: no internet needed. Demo accounts only.</sub>")

        # ----- main app -----
        with gr.Column(visible=False) as app_col:
            with gr.Row(elem_classes="ov-bar", equal_height=True):
                header = gr.Markdown(scale=4)
                btn_logout = gr.Button("Sign out", size="sm", scale=1)
            gr.Markdown(
                "You confirm every item before it counts. Referral rules follow WHO antenatal guidance "
                "(demo rules, pending full extraction). SMS is **simulated** unless a GSM modem is attached."
            )
            with gr.Tabs() as tabs:
                with gr.Tab("1 · Describe", id="describe"):
                    lang = gr.Dropdown(LANG_CHOICES, value="en", label="Language")
                    audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Describe the woman's situation")
                    btn_asr = gr.Button("Transcribe (offline)")
                    transcript = gr.Textbox(label="What was said (you can edit or type it)", lines=4)
                    asr_note = gr.Markdown()
                    btn_extract = gr.Button("Read back for confirmation →", variant="primary", size="lg")
                with gr.Tab("2 · Confirm", id="confirm"):
                    extract_note = gr.Markdown()
                    gr.Markdown("### Read-back: confirm each item")
                    readback = gr.Markdown()
                    with gr.Row():
                        btn_audio = gr.Button("🔊 Play read-back")
                        audio_out = gr.Audio(label="Read-back audio", interactive=False)
                    audio_note = gr.Markdown()
                    ticks = gr.CheckboxGroup(label="Tick each item that is correct")
                    btn_confirm = gr.Button("Confirm ticked items", variant="primary", size="lg")
                    with gr.Accordion("Correct or remove an item", open=False):
                        fld = gr.Dropdown(label="Item")
                        newval = gr.Textbox(label="Correct value (yes / no / severe / mild / light / heavy / a number)")
                        with gr.Row():
                            btn_correct = gr.Button("Correct & confirm")
                            btn_reject = gr.Button("Remove (not true)")
                    gr.Markdown("### Keypad entry (numbers are never taken from voice)")
                    with gr.Row():
                        ga = gr.Number(value=None, label="Gestational age (weeks)", precision=0)
                        sys_ = gr.Number(value=None, label="Systolic BP", precision=0)
                        dia = gr.Number(value=None, label="Diastolic BP", precision=0)
                    with gr.Row():
                        rsys = gr.Number(value=None, label="Repeat systolic", precision=0)
                        rdia = gr.Number(value=None, label="Repeat diastolic", precision=0)
                        pulse = gr.Number(value=None, label="Pulse", precision=0)
                    with gr.Row():
                        temp = gr.Number(value=None, label="Temperature °C")
                        fhr = gr.Number(value=None, label="Fetal heart rate", precision=0)
                    with gr.Row():
                        protein = gr.Dropdown(["negative", "trace", "+", "++", "+++", "unknown"], value=None, label="Urine protein")
                        severe = gr.Dropdown(["No", "Yes", "Don't know"], value=None, label="Severe pre-eclampsia symptoms")
                    btn_keypad = gr.Button("Add keypad entries to read-back")
                    keypad_note = gr.Markdown()
                    gr.Markdown("### Confirmed so far")
                    confirmed = gr.Markdown()
                    preview = gr.Markdown()
                with gr.Tab("3 · Result", id="result"):
                    btn_finish = gr.Button("Finish encounter: discard unconfirmed, apply rules, send referral", variant="primary", size="lg")
                    result = gr.Markdown()
                    sms_out = gr.Markdown()
                    handover = gr.Textbox(label="Handover (confirmed data only)", lines=16)
                with gr.Tab("4 · FHIR & SMS replies", id="fhir"):
                    valid = gr.Markdown()
                    btn_post = gr.Button("POST Bundle to local HAPI FHIR server")
                    post_out = gr.Markdown()
                    reply = gr.Textbox(label="Incoming SMS reply (simulated), e.g. ACK ABCD or FULL ABCD")
                    btn_reply = gr.Button("Receive reply")
                    reply_out = gr.Markdown()
                    bundle = gr.Code(label="FHIR R4 transaction Bundle", language="json")

        login_out = [login_col, app_col, login_msg, header, pin, lang, st]
        btn_login.click(do_login, [who, pin, st], login_out)
        pin.submit(do_login, [who, pin, st], login_out)
        btn_logout.click(do_logout, [st], login_out)

        view_out = [readback, ticks, fld, confirmed, preview]
        btn_asr.click(do_transcribe, [audio, lang, st], [transcript, asr_note, st])
        btn_extract.click(do_extract, [audio, transcript, lang, st],
                          [*view_out, extract_note, transcript, asr_note, tabs, st])
        btn_confirm.click(do_confirm, [ticks, st], [*view_out, st])
        btn_correct.click(do_correct, [fld, newval, st], [*view_out, st])
        btn_reject.click(do_reject, [fld, st], [*view_out, st])
        btn_keypad.click(do_keypad, [ga, sys_, dia, rsys, rdia, pulse, temp, fhr, protein, severe, st], [*view_out, keypad_note, st])
        btn_audio.click(do_readback_audio, [st], [audio_out, audio_note])
        btn_finish.click(do_finish, [st], [result, handover, sms_out, bundle, valid, *view_out, st])
        btn_post.click(do_post_fhir, [st], [post_out, st])
        btn_reply.click(do_reply, [reply, st], [reply_out, st])
    return ui


def _self_signed_cert() -> tuple[str, str]:
    d = Path.home() / ".ovamha"
    d.mkdir(exist_ok=True)
    key, crt = d / "key.pem", d / "cert.pem"
    if not crt.exists():
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30", "-subj", "/CN=ovamha.local",
                        "-keyout", str(key), "-out", str(crt)], check=True, capture_output=True)
    return str(key), str(crt)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--https", action="store_true", help="self-signed HTTPS so phone browsers allow the microphone")
    a = ap.parse_args()
    kw = {}
    if a.https:
        key, crt = _self_signed_cert()
        kw = {"ssl_keyfile": key, "ssl_certfile": crt, "ssl_verify": False}
    build_ui().launch(server_name="0.0.0.0", server_port=a.port, theme=THEME, css=CSS, **kw)


if __name__ == "__main__":
    main()
