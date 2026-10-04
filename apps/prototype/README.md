# Ovamha prototype

Offline pipeline on a laptop (or Raspberry Pi): audio → ASR → field extraction → AI safety net → read-back (text + audio) → worker confirms / corrects (keypad for numbers) → rules → handover → FHIR Bundle → SMS.

## Run

```
make setup        # once, from the repo root (downloads packages)
make test         # 43 tests: rule boundaries, confirmation gate, FHIR, SMS
make run          # open http://localhost:7860, or http://<laptop-ip>:7860 from a phone on the same Wi-Fi
make run-https    # self-signed HTTPS: needed for the phone's microphone (accept the browser warning)
```

The first transcription downloads Whisper small (~460 MB) once; after that, no internet is needed.

## What is real and what is simulated

| Part | Status |
| --- | --- |
| ASR | Real, offline: faster-whisper, `openai/whisper-small`, int8. Fine-tuned English model not yet available. Yoruba uses base Whisper (weak); Krio is decoded as English (fallback). |
| Extraction and safety net | Real: lexicon + regex. English terms are a baseline; **Krio and Yoruba terms are a draft for native-speaker review**. |
| Confirmation gate | Real: only confirmed items reach rules, handover, FHIR and SMS; unconfirmed items are discarded on Finish. |
| Rules | Real code, **demo rules** from the WHO ANC DAK PDF, pending Annex B extraction. |
| Read-back audio | Real, offline: pre-recorded clips from `content/audio/<lang>/` if present, else the system voice (macOS `say` / `espeak-ng`, English only). |
| FHIR Bundle | Real, validated with `fhir.resources` (R4B models). Danger-sign codes are Ovamha placeholders. |
| SMS | **Simulated** (outbox log) unless `OVAMHA_GSM=1` and `gammu` with a GSM modem are present. |

## Modules (`src/ovamha_proto/`)

`asr.py` · `extract.py` + `lexicon.py` · `safety_net.py` · `confirm.py` · `rules.py` · `tts.py` · `handover.py` · `encounter.py` · `fhir_bundle.py` · `fhir_client.py` · `sms.py` · `app.py`

## Demo logins (fictional demo accounts, offline)

| Worker | Username | PIN |
| --- | --- | --- |
| Nurse Fati | fati | 769131 |
| CHW Aminata | aminata | 507892 |
| Midwife Funmi | funmi | 186706 |
