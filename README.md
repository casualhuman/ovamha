# Ovamha: offline voice guidance for safer maternal care

Ovamha (Offline Voice Assistant for Maternal Healthcare in Africa) helps community health workers, nurses and midwives assess a pregnant woman by voice, with no internet. The worker describes the situation; Ovamha writes down what it understood and reads it back for confirmation. It then checks only the **confirmed** facts against **WHO antenatal care guidance and the country's own national guideline**, and **suggests** what to do, citing the exact source. **The health worker decides.** If she refers, Ovamha follows the national referral pathway and produces the referral SMS, a standards-based health record (HL7 FHIR) and a printable referral letter.

Focus countries: Sierra Leone and Nigeria. Prototype for the World Bank Small AI for Development Hackathon (October 2026).

## Try it

**Online (hosted copy for judges):** https://r8086-ovamha.hf.space. The same code, with its speech and voice models inside the container; no external AI service is called. The free host sleeps when idle: the first visit can take about a minute. Records sync to a demo FHIR hub: https://r8086-ovamha-fhir.hf.space/fhir/ServiceRequest

**Offline, on your own machine (how it runs in the field):**

```
make setup     # once, with internet: Python packages and the speech/voice models
make test      # 140 automated tests
make run       # then switch the internet off and open http://localhost:8000
```

Phone on the same Wi-Fi as the laptop "hub": `make run-https` (phone microphones need HTTPS). In the field, a laptop or Raspberry Pi at the health post is the hub and nurses' phones connect to it over local Wi-Fi; nothing needs the internet.

## Test it offline

Three ways, from most realistic to quickest:

1. **Health-post simulation (no internet anywhere).** Turn mobile data **off** on a phone and switch on its hotspot. Connect a laptop to that hotspot and run `make run-https` there. On the phone, open `https://<laptop-ip>:8000`, accept the local certificate, and **Add to Home Screen**: Ovamha installs like an app (own icon, full screen). Everything works: speech, voices, guideline advice, referral letter. The phone and laptop only talk over the local network.
2. **The hosted image, offline.** Run the exact hosted demo locally with Docker, then switch the internet off:
   `docker run -it -p 7860:7860 --platform=linux/amd64 registry.hf.space/r8086-ovamha:latest` → open http://localhost:7860
3. **Automated check in a real browser.** `.venv/bin/python scripts/offline_check.py` (needs `pip install playwright && playwright install chromium`). It runs a check through the hub, then cuts the browser's network completely and reloads: the installed app still opens, keeps the worker signed in, and says *"Can't reach the Ovamha hub. Connect to the health post Wi-Fi. No internet is needed."*

**What runs where:** the phone shows the app; the hub (laptop or Raspberry Pi at the health post) runs speech recognition, read-aloud voices, the guideline rules and the FHIR record store. Nothing calls the internet; the hub uploads records to the district/national level only when a connection exists. A fully on-phone Android version is the production target.

## For judges: demo logins

Fictional demo accounts, checked offline on the device (PINs are stored only as salted hashes).

| Health worker | Username | PIN |
| --- | --- | --- |
| Nurse Fati (Sierra Leone) | `fati` | `769131` |
| CHW Aminata (Sierra Leone) | `aminata` | `507892` |
| Midwife Funmi (Nigeria) | `funmi` | `186706` |

**Demo woman for a returning check:** card number **`MAM-A2A`** (fictional "Mariama Demo", about 20 weeks pregnant, history already recorded: 3 pregnancies, previous pre-eclampsia and caesarean section). She is available on every fresh start, online and offline.

Two things to try:

1. **First visit:** sign in as `fati` → **Guide me** → **First visit** → register her → describe *"She is 28 weeks pregnant, she has seen blood since this morning, a lot of it. She fainted yesterday but she is fine now. No fever."* → confirm → **Check the guidelines** → decide → referral letter.
2. **Returning woman:** **Guide me** → **Returning** → card `MAM-A2A` → describe *"Her head is pounding and she sees stars. Her feet are swollen."* → the history step is skipped (already recorded) → enter BP, e.g. *150 over 100*, and urine protein **++** → **Check the guidelines**: the national guideline flags her previous pre-eclampsia and caesarean section (Table 3.4).

## Standards and guidelines followed

Ovamha does not invent clinical rules or data formats. Three layers are used, each cited inside the app and in the code:

1. **International clinical guidance:** WHO antenatal care recommendations, made computable through the WHO Digital Adaptation Kit (DAK).
2. **National guidelines:** the country's own clinical guideline, encoded as a content file. **Sierra Leone is the worked example**; another country plugs in its own file the same way.
3. **Health data and identity standards:** HL7 FHIR R4, LOINC, UCUM and HL7 terminologies, OpenHIE architecture patterns and World Bank ID4D identity principles.

### 1. WHO antenatal care: the Digital Adaptation Kit (DAK)

| WHO source | How Ovamha uses it | Where |
| --- | --- | --- |
| [WHO recommendations on antenatal care for a positive pregnancy experience (2016)](https://www.who.int/publications/i/item/9789241549912) | Minimum of 8 contacts; the basis of the contact schedule | Next-contact date |
| [WHO DAK for antenatal care (2021)](https://www.who.int/publications/i/item/9789240020306), business process ANC.B | Order of the first contact: registration → quick check (danger signs) → history and profile **only at first contact and only if no danger sign** | [docs/decisions/dak-first-contact.md](docs/decisions/dak-first-contact.md) |
| DAK data elements ANC.A4 (registration) | Name, date of birth or estimated age, address, phone, SMS reminders, emergency contact, co-habitants | [content/questions/anc-registration.json](content/questions/anc-registration.json) |
| DAK data elements ANC.B4 and ANC.B6 (history and profile) | Every question cites its data element, e.g. gravida and outcomes `ANC.B6.DE23–DE26`, past pregnancy complications `ANC.B6.DE34–DE50`, chronic conditions `ANC.B6.DE83–DE99`, tetanus vaccine `ANC.B6.DE100–DE104`, partner HIV status `ANC.B6.DE156–DE161` | [content/questions/anc-profile.json](content/questions/anc-profile.json) |
| DAK decision logic ANC.DT.01, danger signs (Fig. 11 quick check) | Danger signs requiring referral | [rules.py](apps/prototype/src/ovamha_proto/rules.py) |
| DAK pre-eclampsia worked example (Table 12) | Pre-eclampsia rule with boundary tests (139/140, 159/160, 89/90, 109/110, protein + vs ++, missing repeat reading) | [tests/rules/test_rules.py](tests/rules/test_rules.py) |
| [WHO SMART ANC FHIR implementation guide](http://build.fhir.org/ig/WorldHealthOrganization/smart-anc/) | Resource model and the PlanDefinition reference `ANCDT01` in each rule result | [fhir_bundle.py](apps/prototype/src/ovamha_proto/fhir_bundle.py) |

### 2. National guideline: Sierra Leone as the worked example

The **Sierra Leone Integrated Obstetric and Newborn Care Guideline** (Ministry of Health, copy-edited draft of 19 January 2026) is encoded in [content/guidelines/sierra-leone-iong-2026.json](content/guidelines/sierra-leone-iong-2026.json). Only content Ovamha can evaluate from confirmed data is encoded, and every item carries its table or section.

| Guideline section | What Ovamha does with it |
| --- | --- |
| Table 3.2 Schedule of contacts (8 contacts: 12, 20, 26, 30, 34, 36, 38, 40 weeks) | Works out the next contact date from gestational age |
| Table 3.3 Danger signs in pregnancy | Suggests urgent referral when a listed sign is confirmed |
| Pre-eclampsia classification after 20 weeks | Classifies pre-eclampsia, severe pre-eclampsia and eclampsia; includes *"if severe pre-eclampsia is suspected, do not wait 4 hours to repeat the BP"* |
| Table 3.4 Referral pathway for high-risk pregnancy | Suggests the right action **for the worker's facility level** (MCHP, CHP, CHC, BEmONC vs CEmONC) |
| Referral section (minimum requirements; roles of the referring worker) | Referral pathway: informed consent, pre-referral actions, iSBAR call script, call and ambulance times, referral form with a feedback slip for the receiving facility |

**Cited examples, as the worker sees them:**

| Confirmed facts | Suggestion shown | Source cited |
| --- | --- | --- |
| Vaginal bleeding | "Danger sign in pregnancy: assess and stabilise, then consider urgent referral to a CEmONC facility." | Sierra Leone guideline, Table 3.3; WHO DAK ANC.DT.01 |
| BP 165/100 with urine protein ++ | "Life-threatening emergency. Stabilise and start magnesium sulphate per your level of care, then refer to a CEmONC facility for delivery and further management. Do not wait 4 hours to repeat BP." | Sierra Leone guideline, pre-eclampsia classification |
| Previous caesarean section, at a CHP | "If at a lower facility: refer to CEmONC for further assessment… counsel and prepare her for referral for delivery at a CEmONC facility." | Sierra Leone guideline, Table 3.4 |
| Sickle-cell disease, at a CHP | "If at a lower facility: referral to a CEmONC facility for advanced care." | Sierra Leone guideline, Table 3.4 |
| 22 weeks pregnant | "Contact 3 at 26 weeks, around …" | Sierra Leone guideline, Table 3.2 |

Where the guideline does not define a threshold, Ovamha states its assumption on screen and in the file (adolescent = under 20 years; high parity = 5 or more births; fetal heart rate normal range 110–160/min, from the guideline's intrapartum chapter). These need Ministry confirmation.

**Adapting to another country (e.g. Nigeria):** add a guideline file in the same format, with that country's tables and citations. The app, the rules engine and the referral workflow stay the same. Nigeria's national guideline is not encoded yet.

### 3. Health data, terminology and identity standards

| Standard | How Ovamha uses it |
| --- | --- |
| [HL7 FHIR R4](https://hl7.org/fhir/R4/) | Every encounter becomes a transaction Bundle: Patient, EpisodeOfCare, Encounter, Observation, GuidanceResponse, ServiceRequest, Task, Communication, Consent, Provenance, Organization, PractitionerRole, Device. Example: [fhir/examples/referral-bundle.json](fhir/examples/referral-bundle.json). **Official HL7 FHIR Validator: 0 errors, 0 warnings** ([result](ml/eval/results/fhir-validation.md)); the blood pressure reading passes the FHIR vital-signs BP profile |
| [LOINC](https://loinc.org/) | Blood pressure panel 85354-9, systolic 8480-6, diastolic 8462-4, last menstrual period 8665-2 |
| [UCUM](https://ucum.org/) | Units of measure (mm[Hg], Cel, /min, wk) |
| HL7 terminology | Provenance participant types (verifier, assembler, author), consent scope, data-absent-reason (`asked-unknown` for "Don't know"), confidentiality (`R`, restricted, on partner HIV status) |
| FHIR conditional create (`ifNoneExist`) and `If-Match` | Uploads are safe to retry without duplicates; referral status changes cannot overwrite newer data |
| [OpenHIE architecture](https://guides.ohie.org/arch-spec/architecture-specification/standards-and-profiles.md) | Device → facility hub → national systems design, with a mediator for national exchange (see the architecture document) |
| [World Bank ID4D principles](https://id4d.worldbank.org/principles) | Ovamha creates its own woman ID and card number; the national ID is optional, consented, never stored as a number and never used as a key or sent by SMS |

## How it works

```
Speak → What we understood (worker confirms each item) → Her history (first contact only)
      → Measurements (keypad or voice) → Guideline advice (cited) → Worker's decision
      → Referral pathway (consent, checklist, iSBAR call) → SMS + FHIR record + referral letter
```

- **AI where it helps, rules where it matters.** Speech recognition, extraction and an add-only safety net propose; the worker confirms; guideline rules (not a generative model) produce the advice. Why: [docs/decisions/guideline-advice-not-fine-tuning.md](docs/decisions/guideline-advice-not-fine-tuning.md).
- **Nothing unconfirmed counts.** Unconfirmed items are discarded before any rule, record, SMS or sync.
- **Unknown is never normal.** "Don't know" is recorded as unknown.
- **The worker decides.** Declining a suggested referral needs a written or spoken reason; the advice is never hidden.

## What works now (all offline)

- Offline sign-in (username + PIN, hashed on the device)
- Registration with national ID asked first; card number with a check character that catches typos
- First-contact history per DAK ANC.B6
- Voice description with speech recognition (Whisper small), extraction that understands common everyday phrasings, and an add-only AI safety net
- Numbers by keypad or voice; read-aloud in English, Krio and Yoruba voices (MMS-TTS)
- Cited guideline advice (WHO DAK and the Sierra Leone guideline); the worker's decision is recorded
- Referral pathway, simulated referral SMS with ACK/FULL replies, printable referral letter with feedback slip
- FHIR R4 records that pass the official HL7 validator with 0 errors and 0 warnings, and a device outbox that syncs to the hub FHIR server when reachable

## Honest limits

- Krio and Yoruba speech recognition and read-back wording still need native-speaker data
- WHO DAK rules are demo rules from the DAK PDF; danger-sign and profile codes are Ovamha placeholders until the DAK annex spreadsheets are extracted and replaced with WHO SMART ANC codes
- The Sierra Leone guideline used is a January 2026 draft; the Ministry's national standardized referral form layout was not available
- SMS is simulated without a GSM modem; the hub FHIR server (HAPI) needs Docker
- FHIR records validate against base R4, not yet against WHO SMART ANC profiles
- No measured accuracy yet: evaluation protocol in [ml/eval/](ml/eval/)

## Key documents

- [docs/architecture/README.md](docs/architecture/README.md): **backend architecture specification** (tiers, FHIR resource model, identity, sync, SMS, security, AI provenance)
- [docs/decisions/dak-first-contact.md](docs/decisions/dak-first-contact.md): element-by-element alignment with the WHO ANC DAK
- [docs/decisions/guideline-advice-not-fine-tuning.md](docs/decisions/guideline-advice-not-fine-tuning.md): why cited guideline rules, and why the worker decides
- [docs/decisions/agent-handover.md](docs/decisions/agent-handover.md): project brief and design decisions
