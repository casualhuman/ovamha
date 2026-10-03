# Ovamha — Agent Handover

Read this whole note before writing code. It is the single source of context for this task.

## 1. What we are building

**Ovamha (Offline Voice Assistant for Maternal Healthcare in Africa)** is an offline voice assistant for community health workers (CHWs), nurses and midwives. A worker describes a pregnant woman's situation by voice. Ovamha transcribes it, structures it, reads critical values back for confirmation, applies WHO danger-sign and referral rules to the confirmed data, prepares a handover, and sends a referral notice by SMS. It must work with no internet.

Focus countries are Sierra Leone and Nigeria. Demo languages are **Yoruba, Krio and English**.

## 2. The deadline and what is judged

- **Event.** World Bank Group Small AI for Development Hackathon, Health category. The 24-hour hackathon runs **3 to 4 October 2026**; submissions go through the Hack-Nation portal. Check the portal for exact formats (video length, repo or file upload); the portal overrides this note.
- **Required deliverables.** A working small AI prototype; a demo video; documentation of the problem, users and operating constraints; evidence of IP compliance (list every third-party source); English.
- **Judging.** Development relevance; suitability for constrained environments; design, accessibility and inclusivity; practicality and local relevance; responsible AI; recognition of technical and social trade-offs; scaling potential. Entries are "not assessed solely on technical sophistication".
- **Winners are asked** "What does localizing AI development mean for you?"

**Priority rule.** One scenario working end to end, offline, on camera, beats a large unfinished codebase.

## 3. Design decisions already made (do not reopen)

1. **Rules set the floor, AI widens the net, the worker confirms.** WHO and national rules decide referrals. AI transcribes, structures, flags danger signs mentioned in passing, and suggests the next question. AI may add concern; it may never remove, delay or override a rule's prompt.
2. **Nothing unconfirmed counts.** Every critical value is read back and confirmed. Only confirmed data reaches a rule, a handover, an SMS or a sync. Unconfirmed AI output is discarded.
3. **Numbers by keypad.** Blood pressure, pulse, temperature, fetal heart rate and cervical dilatation default to keypad entry. Voice is for symptoms and history.
4. **No live generated advice to the woman.** Patient guidance is pre-approved text or recordings only.
5. **Offline first.** Everything needed during an encounter runs on the device or hub with no internet.
6. **SMS only for messaging.** Referral notices, acknowledgements (ACK / FULL) and appointment reminders. No WhatsApp. SMS carries an encounter code, never the woman's name or HIV status.
7. **Clinical content comes from the WHO Digital Adaptation Kit (DAK) for antenatal care.** Data model is **HL7 FHIR R4**, reusing WHO SMART ANC profiles and codes where possible.
8. **History questions are tiered.** Danger sign present: refer immediately, no history first. Otherwise ask only what the current rules need. "Don't know" is recorded as unknown, never treated as normal.
9. **Identity.** Ovamha creates its own woman ID (UUID) and a short card code at first contact. National ID is optional, consented, and linked via a token or verification reference, never used as a key (World Bank ID4D guidance).
10. **Licences.** Do not block work on licence questions. Do list every dataset, model and WHO source in `THIRD_PARTY.md` (that list is the IP-compliance deliverable).

## 4. Where we are

| Item | Status |
| --- | --- |
| PRD | Done, in Claude Docs (owner will export to PDF for `docs/prd/`) |
| Backend architecture specification v0.1 | Done, in Claude Docs (export to `docs/architecture/`). Covers tiers, standards, FHIR resource model, database design, identity, sync, SMS, security, AI provenance, a reference FHIR transaction, conformance tests |
| ASR fine-tuning notebook (Kaggle) | Written: Whisper small English on AfriSpeech-200 clinical clips, leakage checks, noise augmentation, WER and danger-term recall, int8 CTranslate2 conversion. Run status unknown; ask the owner for results |
| Repo | Structure agreed (section 6). No application code yet |
| DAK Annex A/B spreadsheets | Not downloaded. Use the rules from the DAK PDF for the demo (section 7) and label them as demo rules pending Annex B extraction |
| Krio ASR weights (Khaya AI DONDO) | Access not confirmed. Use a fallback (section 8) |
| Android app | Production target only. Not for this hackathon |

## 5. What to build in the time available

Work in this order. Stop and report after each P0 item is working.

### P0-1. Prototype pipeline (`apps/prototype/`)

A Python app running the whole chain offline on a laptop or Raspberry Pi, with a Gradio (or Streamlit) interface that a phone can open over local Wi-Fi.

Chain: microphone or uploaded audio → ASR → field extraction → AI safety-net flags → read-back (text and audio) → worker confirms or corrects (keypad for numbers) → rules → result → handover → FHIR Bundle → SMS.

| Module | Responsibility | Acceptance |
| --- | --- | --- |
| `asr.py` | faster-whisper (CTranslate2 int8). English: fine-tuned model from the notebook if available, else `openai/whisper-small`. Language selectable | Transcribes the demo scenario audio offline |
| `extract.py` | Transcript → fields: gestational age, bleeding (yes/amount), dizziness, fainting, headache, visual disturbance, convulsions, fever, abdominal pain, breathing difficulty. Start with a lexicon and regex per language; LLM optional (P2) | Every field is filled or explicitly "not captured" |
| `safety_net.py` | Scans the full transcript for danger-sign terms not already captured as fields; returns flags to confirm | Flags "fainted" in "she fainted yesterday but is fine now" |
| `confirm.py` | Builds the read-back list; holds proposed vs confirmed state; discards unconfirmed | No field reaches rules without a confirm event |
| `rules.py` | Demo rules from section 7, pure functions on confirmed data, each citing its DAK source | Unit tests pass, including boundary values |
| `tts.py` | Read-back audio. Use pre-recorded clips if available, else an offline TTS (e.g. MMS-TTS via transformers; check model availability per language) | Plays read-back offline |
| `handover.py` | Handover text separating reported symptoms, measured observations, actions; FHIR Bundle (P0-2) | Contains only confirmed fields |
| `sms.py` | Sends the referral SMS through a GSM modem (Gammu) if present, else writes to a simulated outbox log shown in the UI | SMS text appears; an "ACK R7K2" reply updates referral status |
| `app.py` | Gradio UI: record, review read-back, confirm, see rule result, see handover and SMS | Demo scenario runs end to end with Wi-Fi only (no internet) |

### P0-2. FHIR slice (to show standards competence)

Make the prototype emit and exchange real FHIR, validated.

1. Build an R4 **transaction Bundle** from the confirmed encounter: Patient (identifiers: Ovamha UUID, card code), Encounter, Observations (BP panel LOINC 85354-9 with 8480-6 / 8462-4; danger-sign Observations), GuidanceResponse (rule fired: canonical `http://fhir.org/guides/who/anc-cds/PlanDefinition/ANCDT01`), ServiceRequest (urgent referral), Task (status `requested`), Provenance (verifier = worker, assembler = ASR model Device, activity = `spoken-ai-extracted-confirmed`). Follow section 13 of the architecture specification.
2. Validate it. Use the Python `fhir.resources` library for structural validation in code, and the official HL7 FHIR Validator (`validator_cli.jar`) against base R4 in a script. Show zero errors.
3. Run a local **HAPI FHIR server** in Docker (`hapiproject/hapi`) on the laptop or Pi. POST the Bundle; show the resources via the FHIR REST API (e.g. `GET /Patient/{id}/$everything` or a search for Observations).
4. On simulated ACK SMS, PUT the Task to `accepted`; on FULL, to `rejected`. Show the status change via the API.
5. Save the example Bundle to `fhir/examples/referral-bundle.json`.

Danger-sign codes: use placeholders in an Ovamha code system (`https://fhir.ovamha.org/CodeSystem/danger-signs`) mapped to the DAK quick-check names, and state in the README that SMART ANC codes replace them after Annex extraction. Do not invent SNOMED or LOINC codes; only the LOINC codes listed above are confirmed.

### P0-3. Demo scenario and video support

- Script the scenario in `demo/scenarios/bleeding-28-weeks.md`: a CHW reports heavy vaginal bleeding at 28 weeks in Krio or Yoruba (English fallback), mentions in passing that the woman fainted; AI flags fainting; worker confirms; BP 90/60 entered by keypad; DT.01 fires; urgent referral; handover; SMS; ACK received; Task accepted.
- Record audio clips for the scenario in each language available.
- Capture screenshots for `demo/screenshots/`.

### P1

- `README.md` following the outline in section 9.
- `THIRD_PARTY.md` (section 10).
- `ml/eval/results/` from the notebook output (WER, danger-term recall, test-set size, int8 vs full). Report only measured numbers.
- `tests/rules/` boundary tests; `tests/prototype/` for the confirmation gate.
- Real SMS through a SIM modem on the Pi, if hardware is available.

### P2 (only if time remains)

- Yoruba ASR: convert `LyngualLabs/whisper-small-yoruba` (Apache 2.0) to CTranslate2 int8.
- Krio ASR: `facebook/mms-1b-all` with the `kri` adapter via transformers (fallback); DONDO if weights become available.
- Small LLM for extraction and safety net via llama.cpp (grammar-constrained JSON).
- Labour Care Guide loop (simplified).

## 6. Repo structure

Create this layout. Folders not used in the hackathon get a one-line README.

```
ovamha/
├── README.md  LICENSE  THIRD_PARTY.md  .gitignore  .env.example  Makefile
├── docs/ {prd, architecture, diagrams, decisions}
├── demo/ {video-link.md, screenshots/, scenarios/}
├── apps/
│   ├── prototype/ {src/ovamha_proto/*.py, requirements.txt, README.md}
│   └── android/README.md           (production target, later)
├── hub/ {fhir-server, mediator/adapters, sms-gateway, indicator-engine, db/migrations, docker-compose.yml}
├── district-server/README.md       (later)
├── ml/ {notebooks, src/ovamha_ml, eval/{term_lists, results}, models/README.md}
├── content/ {dak, rules, questions, guidance-cards/{en,yo,kri}, sms-templates, audio/README.md}
├── fhir/ {ig, examples}
├── tests/ {rules, sync, prototype}
├── data/README.md                  (no data committed)
└── scripts/ {download_data.sh, convert_ct2.sh, generate_rule_tests.py, setup_pi.sh}
```

Never commit data, model weights, audio or secrets.

## 7. Demo rules (from the DAK PDF; label as pending Annex B extraction)

**ANC.DT.01 Danger signs requiring referral (DAK Fig. 11 quick check).** Any of: unconscious; convulsing; vaginal bleeding; severe abdominal pain; looks very ill; headache with visual disturbance; severe difficulty breathing; central cyanosis; fever; severe vomiting; severe pain; imminent delivery; labour. Action: urgent referral; rapid assessment; call for help.

**Pre-eclampsia (DAK Table 12, worked example; numbered ANC.DT.16 in Table 12 and ANC.DT.17 in Table 10 — cite by name).** IF systolic 140 to <160 mmHg OR diastolic 90 to <110 mmHg, AND a repeat reading is in the same range, AND no symptoms of severe pre-eclampsia, AND urine protein ++ or +++ → pre-eclampsia; refer urgently to hospital; revise birth plan.

Boundary tests must cover 139/140 and 159/160 systolic, 89/90 and 109/110 diastolic, proteinuria + vs ++, and missing repeat reading (must prompt for it, not assume).

**Derived values.** GA (weeks) = (today − LMP) / 7. EDD = LMP + 280 days.

**Missing data.** Unknown is never normal. If a rule needs a value that is missing, prompt for it.

## 8. Models and data

| Language | ASR for the prototype | Notes |
| --- | --- | --- |
| English | Fine-tuned Whisper small from the notebook, else `openai/whisper-small` (MIT) | Notebook trains on AfriSpeech-200 clinical clips |
| Yoruba | `LyngualLabs/whisper-small-yoruba` (Apache 2.0, Yoruba–English code-switched, 20.76% WER on its own test set) | Convert to CTranslate2 int8 |
| Krio | `facebook/mms-1b-all`, adapter `kri` (CC-BY-NC 4.0) | DONDO (Khaya AI, Apache 2.0) preferred if weights confirmed |

Do not use speech enhancement by default (it degraded medical ASR in every configuration of Chondhekar et al.). Capture 16 kHz mono; use a quality gate (VAD, clipping, SNR) and ask to repeat on failure.

## 9. README outline (one section per judging criterion)

1. Ovamha in one line + demo video link
2. Problem and users
3. Operating constraints (no connectivity, 2G/SMS, low-cost Android, three languages, low literacy)
4. How it works (architecture diagram; rules floor, AI net, worker confirms)
5. What is working now (exact; separate built from designed)
6. Results (measured numbers only, with test-set size)
7. FHIR and interoperability (validated Bundle, HAPI round trip, Task status via SMS)
8. Responsible AI and trade-offs (confirmation, keypad, add-only AI, SMS minimisation, limitations)
9. Local relevance and scaling (WHO DAK, open standards, deployment modes A/B/C)
10. What localizing AI development means for us
11. Team

## 10. THIRD_PARTY.md must list

WHO DAK for antenatal care (2021); WHO SMART ANC implementation guide; AfriSpeech-200; Whisper; LyngualLabs whisper-small-yoruba; MMS (ASR and TTS); DONDO if used; faster-whisper / CTranslate2; HAPI FHIR; Gradio; HL7 FHIR Validator; fhir.resources; any other library or model actually used. Give source link and licence for each.

## 11. Rules for the agent

- Do not fabricate results, metrics or validation outcomes. If something is simulated (SMS, codes, rules pending extraction), label it in the UI and README.
- Keep every claim verifiable from the repo.
- Prefer working and small over complete and broken.
- Ask the owner before changing any decision in section 3.
- Report progress after each P0 item with what runs and how to run it.

## 12. Key references

- WHO DAK for antenatal care: https://www.who.int/publications/i/item/9789240020306
- WHO SMART ANC IG: http://build.fhir.org/ig/WorldHealthOrganization/smart-anc/
- OpenHIE standards and profiles: https://guides.ohie.org/arch-spec/architecture-specification/standards-and-profiles.md
- HAPI FHIR: https://hapifhir.io/
- Android FHIR SDK: https://developers.google.com/open-health-stack/android-fhir
- World Bank ID4D principles: https://id4d.worldbank.org/principles
- Hackathon details: https://opportunitiesforyouth.org/2026/09/02/world-bank-small-ai-for-development-hackathon-2026-build-inclusive-ai-solutions-and-win-sponsored-travel-to-seoul/
