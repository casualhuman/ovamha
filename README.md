# Ovamha: offline voice guidance for safer maternal care

Ovamha (Offline Voice Assistant for Maternal Healthcare in Africa) helps community health workers, nurses and midwives assess a pregnant woman by voice, with no internet. The worker describes the situation; Ovamha writes down what it understood and reads it back for confirmation. It then checks only the **confirmed** facts against **WHO antenatal care guidance and the country's own national guideline**, and **suggests** what to do, citing the exact source. **The health worker decides.** If she refers, Ovamha follows the national referral pathway and produces the referral SMS, a standards-based health record (HL7 FHIR) and a printable referral letter.

Focus countries: Sierra Leone and Nigeria. Prototype for the World Bank Small AI for Development Hackathon (October 2026).

**Contents:** [Try it](#try-it) · [The problem](#the-problem-and-who-it-is-for) · [Built for low connectivity and low-end devices](#built-for-no-or-low-connectivity-and-low-end-devices) · [How it works](#how-it-works) · [Judging criteria](#how-ovamha-meets-the-judging-criteria) · [Digital public infrastructure](#digital-public-infrastructure-and-the-world-bank) · [What works now](#what-works-now-all-offline) · [Limits and trade-offs](#honest-limits-and-trade-offs) · [Third-party sources](#third-party-sources-and-licences) · [All documentation](#documentation)

## Try it

**Online (hosted copy for judges):** https://r8086-ovamha.hf.space. The same code, with its speech and voice models inside the container; no external AI service is called. The free host sleeps when idle: the first visit can take about a minute. Records sync to a demo FHIR hub: https://r8086-ovamha-fhir.hf.space/fhir/ServiceRequest

**Offline, on your own machine (how it runs in the field):**

```
make setup     # once, with internet: Python packages and the speech/voice models
make test      # 173 automated tests
make run       # then switch the internet off and open http://localhost:8000
```

Phone on the same Wi-Fi as the laptop "hub": `make run-https` (phone microphones need HTTPS). In the field, a laptop or Raspberry Pi at the health post is the hub and nurses' phones connect to it over local Wi-Fi; nothing needs the internet.

## Demo script

[docs/demo/point-of-care-demo.md](docs/demo/point-of-care-demo.md): a five-minute point-of-care demo with one woman at two moments (a routine visit where the guideline's suggestions do the work, then an emergency), with what to tap and what to say at each step.

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

## Test it offline

Three ways, from most realistic to quickest:

1. **Health-post simulation (no internet anywhere).** Turn mobile data **off** on a phone and switch on its hotspot. Connect a laptop to that hotspot and run `make run-https` there. On the phone, open `https://<laptop-ip>:8000`, accept the local certificate, and **Add to Home Screen**: Ovamha installs like an app (own icon, full screen). Everything works: speech, voices, guideline advice, referral letter. The phone and laptop only talk over the local network.
2. **The hosted image, offline.** Run the exact hosted demo locally with Docker, then switch the internet off:
   `docker run -it -p 7860:7860 --platform=linux/amd64 registry.hf.space/r8086-ovamha:latest` → open http://localhost:7860
3. **Automated check in a real browser.** `.venv/bin/python scripts/offline_check.py` (needs `pip install playwright && playwright install chromium`). It runs a check through the hub, then cuts the browser's network completely and reloads: the installed app still opens, keeps the worker signed in, and says *"Can't reach the Ovamha hub. Connect to the health post Wi-Fi. No internet is needed."*

**What runs where:** the phone shows the app; the hub (laptop or Raspberry Pi at the health post) runs speech recognition, read-aloud voices, the guideline rules and the FHIR record store. Nothing calls the internet; the hub uploads records to the district/national level only when a connection exists. A fully on-phone Android version is the production target.

## The problem and who it is for

Nigeria accounted for **28.7% of all maternal deaths worldwide in 2023** (about 75,000 women; 993 deaths per 100,000 live births). Sierra Leone cut its maternal mortality ratio by 78% since 2000, but at 354 per 100,000 it is still almost twice the global average of 197 ([WHO, UNICEF, UNFPA, World Bank Group and UNDESA, *Trends in maternal mortality 2000 to 2023*, 2025](https://iris.who.int/server/api/core/bitstreams/29f43a3d-2228-489c-b1e7-b2f28e9101ce/content)). Many of these deaths follow danger signs that were present, but not recognised or acted on in time.

**Users:** community health workers, nurses and midwives at health posts and primary health centres, often with no internet, intermittent power, a basic Android phone, and patients who speak Krio, Yoruba or English. **What changes:** the worker describes the woman in her own words; Ovamha catches danger signs she mentions, checks them against WHO and national guidance, and gets a referral, SMS and record out in minutes, all without a connection.

## Built for no or low connectivity and low-end devices

| Constraint | How Ovamha handles it |
| --- | --- |
| **No internet** | Every step of an encounter runs offline: speech recognition, danger-sign detection, read-aloud, guideline rules, records. Proven with the network cut ([offline check](ml/eval/results/offline-reload.png)) |
| **Intermittent connectivity** | Finished records wait in an encrypted outbox on the device and sync to the facility hub automatically when reachable; uploads are safe to retry (FHIR conditional create) |
| **2G or SMS only** | Referral notices and the receiving facility's ACK/FULL replies go by plain SMS; no data plan or WhatsApp needed |
| **Low-end phones** | The phone only needs a browser: the app installs to the home screen (PWA) and the AI runs on a small local hub (laptop or Raspberry Pi 5 at the health post) over the health post's Wi-Fi. A fully on-phone Android version is the production target |
| **Small models, no cloud** | Speech: Whisper small, int8, about 250 MB, 2 to 3 times faster than real time on 4 CPU threads (measured in the notebook). Danger signs: a 90 MB sentence encoder on CPU. Voices: MMS-TTS. No GPU, no cloud, no per-use AI fees |
| **Low literacy, busy clinics** | Speak instead of type; everything understood is read back aloud; numbers by keypad or voice; large touch targets |
| **Three languages** | English, Krio and Yoruba read-aloud; Krio and Yoruba speech recognition and wording need native-speaker data (see [limits](#honest-limits-and-trade-offs)) |
| **No national health information exchange** | Works in three deployment modes: with a national exchange, with separate national systems, or with none, and moves between them without data conversion ([architecture 3.3](docs/architecture/README.md)) |
| **Power** | Designed for a hub on backup power; not yet measured on battery |

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


More: [docs/ai/README.md](docs/ai/README.md) (the AI and its measured results) · [docs/guidelines/README.md](docs/guidelines/README.md) (every guideline used, with citations) · [docs/architecture/README.md](docs/architecture/README.md) (full design).

## How Ovamha meets the judging criteria

| Criterion | Evidence |
| --- | --- |
| **Development relevance** | Maternal deaths in Nigeria and Sierra Leone ([the problem](#the-problem-and-who-it-is-for)); follows WHO antenatal care guidance (DAK) and Sierra Leone's national obstetric guideline, so the advice matches what the ministry already expects ([guidelines](docs/guidelines/README.md)) |
| **Suitability for constrained environments** | Fully offline, SMS, low-cost hub, small CPU models, works with or without national systems ([table above](#built-for-no-or-low-connectivity-and-low-end-devices)) |
| **Design, accessibility and inclusivity** | Voice first with read-aloud for low literacy; Krio and Yoruba alongside English; plain wording; privacy notice read to the woman before registration; she can see her own record |
| **Practicality and local relevance** | Uses the national referral pathway (consent, pre-referral checklist, iSBAR call, referral letter with feedback slip); facility-level-aware advice; card number for women without national ID; demo runs end to end on a laptop and phone |
| **Responsible AI** | AI proposes, the worker confirms, cited rules advise, the worker decides; AI can add a concern but never remove one; every proposal shows its evidence; voice deleted and never used for training; WHO AI-ethics principles mapped ([AI](docs/ai/README.md), [privacy](docs/privacy/README.md)) |
| **Technical and social trade-offs** | Recall favoured over precision because the worker checks everything; keypad for numbers because speech errors on numbers are dangerous; rules instead of a generative model for advice; results and limits stated plainly ([limits](#honest-limits-and-trade-offs)) |
| **Scaling potential** | A new country adds a guideline file and language models; FHIR R4 and OpenHIE fit national systems; builds on digital public infrastructure ([DPI](#digital-public-infrastructure-and-the-world-bank)) |

## Digital public infrastructure and the World Bank

The World Bank treats **digital identity, trusted data sharing and digital payments** as the foundational building blocks of digital public infrastructure (DPI), built to be interoperable, open, modular, inclusive and private by design ([*Digital Public Infrastructure and Development: A World Bank Group Approach*, 2025](https://documents1.worldbank.org/curated/en/099031025172027713/pdf/P505739-84c5073b-9d40-4b83-a211-98b2263e87dd.pdf)). Ovamha is a health service designed to **sit on top of DPI rather than rebuild it**:

- **Identity:** its own functional ID and card number so care never waits for an ID document; the national ID (NIN) is linked only with consent and never stored as a number or used as a key, following the World Bank's [ID4D principles](https://id4d.worldbank.org/principles).
- **Data sharing:** every encounter is an HL7 FHIR R4 record (official validator: 0 errors, 0 warnings) exchanged through a facility hub and mediator, following OpenHIE, so it can feed a national health information exchange or HMIS when one exists.
- **Payments:** not used.
- **Principles:** open standards, modular country content, inclusive voice design, privacy and security by design, provenance on every record. It also follows the [Principles for Digital Development](https://digitalprinciples.org/), which the World Bank endorsed.

Full mapping: [docs/standards/README.md](docs/standards/README.md).

## What works now (all offline)

- Offline sign-in (username + PIN, hashed on the device)
- Registration with national ID asked first; card number with a check character that catches typos
- First-contact history per DAK ANC.B6
- Voice description with speech recognition (Whisper small), extraction that understands common everyday phrasings, and an add-only AI safety net
- Numbers by keypad or voice; read-aloud in English, Krio and Yoruba voices (MMS-TTS)
- Cited guideline advice (WHO DAK and the Sierra Leone guideline); the worker's decision is recorded
- Referral pathway, simulated referral SMS with ACK/FULL replies, printable referral letter with feedback slip
- FHIR R4 records that pass the official HL7 validator with 0 errors and 0 warnings, and a device outbox that syncs to the hub FHIR server when reachable


## Honest limits and trade-offs

- **Danger-sign detection was measured on written text, not speech:** the text classifier catches 94% of danger signs on 200 held-out descriptions, but these were AI-written, so real spoken descriptions will score lower ([AI](docs/ai/README.md))
- **Speech recognition fine-tuning is at smoke-test stage** (accented English WER 40% → 30% on 200 clips); full runs pending ([notebook](ml/notebooks/README.md))
- **Krio and Yoruba** speech recognition, danger-sign words and read-back wording still need native-speaker data and review; the text classifier is English only
- **Not yet measured on a Raspberry Pi, a low-end phone or battery power**
- WHO DAK rules are demo rules from the DAK PDF; danger-sign and profile codes are Ovamha placeholders until the DAK annex spreadsheets are extracted and replaced with WHO SMART ANC codes
- The Sierra Leone guideline used is a January 2026 draft; Nigeria's national guideline is not encoded yet ([placeholder](docs/guidelines/README.md#4-nigeria-placeholder))
- SMS is simulated without a GSM modem; the hub FHIR server (HAPI) needs Docker
- FHIR records validate against base R4, not yet against WHO SMART ANC profiles
- Privacy controls are prototype-level: hardware-backed keys, TLS on every link and role-based access are planned ([privacy](docs/privacy/README.md))

## Third-party sources and licences

| Source | Used for | Licence |
| --- | --- | --- |
| [OpenAI Whisper small](https://huggingface.co/openai/whisper-small) via [Systran faster-whisper-small](https://huggingface.co/Systran/faster-whisper-small) | Speech recognition | Apache-2.0 / MIT |
| [LyngualLabs whisper-small-yoruba](https://huggingface.co/LyngualLabs/whisper-small-yoruba) | Yoruba speech recognition (notebook) | Apache-2.0 |
| [Meta MMS-TTS](https://huggingface.co/facebook/mms-tts-eng) (eng, kri, yor) | Read-aloud voices | **CC BY-NC 4.0 (non-commercial)** |
| [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Danger-sign text classifier (fine-tuned) | Apache-2.0 |
| [AfriSpeech-200](https://huggingface.co/datasets/intronhealth/afrispeech-200) | Speech fine-tuning; 100 transcripts in the text evaluation set | **CC BY-NC-SA 4.0 (non-commercial)** |
| [Google FLEURS](https://huggingface.co/datasets/google/fleurs) | Yoruba speech fine-tuning | CC BY 4.0 |
| [WHO ANC Digital Adaptation Kit](https://www.who.int/publications/i/item/9789240020306) and [WHO ANC recommendations](https://www.who.int/publications/i/item/9789241549912) | Clinical content, data elements, decision logic | CC BY-NC-SA 3.0 IGO |
| Sierra Leone Integrated Obstetric and Newborn Care Guideline (MoHS, 2026 draft) | National guideline content | Ministry of Health document; use for this prototype to be confirmed with the Ministry |
| HL7 FHIR, LOINC, UCUM | Data standards | Free to use under their terms |
| Python packages (FastAPI, faster-whisper, transformers, PyTorch, cryptography, fhir.resources) | Software | Open-source licences |

Non-commercial licences (MMS-TTS, AfriSpeech-200, WHO DAK) suit this prototype; any commercial use needs replacements or permission. The Ovamha repository does not have a licence file yet.

## Documentation

**Topic guides**

| README | What it covers |
| --- | --- |
| [docs/guidelines/README.md](docs/guidelines/README.md) | Clinical guidelines: WHO ANC DAK, Sierra Leone national guideline, how to add a country, Nigeria placeholder |
| [docs/ai/README.md](docs/ai/README.md) | The AI models, danger-sign detection results, WHO responsible-AI principles |
| [docs/privacy/README.md](docs/privacy/README.md) | Privacy and data protection: international, Africa (ECOWAS, AU), Sierra Leone and Nigeria; where each measure is in the code; DPIA, policy, breach plan, voice data |
| [docs/standards/README.md](docs/standards/README.md) | Health data standards (FHIR, LOINC, UCUM, OpenHIE, ID4D) and digital public infrastructure alignment |
| [docs/architecture/README.md](docs/architecture/README.md) | Full backend architecture specification |

**Decisions and demo**

- [docs/demo/point-of-care-demo.md](docs/demo/point-of-care-demo.md): five-minute demo script
- [docs/decisions/dak-first-contact.md](docs/decisions/dak-first-contact.md): element-by-element alignment with the WHO ANC DAK
- [docs/decisions/guideline-advice-not-fine-tuning.md](docs/decisions/guideline-advice-not-fine-tuning.md): why cited guideline rules, and why the worker decides
- [docs/decisions/agent-handover.md](docs/decisions/agent-handover.md): project brief and design decisions
- [docs/prd/README.md](docs/prd/README.md): product requirements

**Privacy documents:** [voice data](docs/privacy/voice-data.md) · [DPIA](docs/privacy/dpia.md) · [privacy design policy](docs/privacy/privacy-design-policy.md) · [breach response](docs/privacy/breach-response.md)

**AI and evaluation:** [text classifier](ml/textclf/README.md) · [speech fine-tuning notebook](ml/notebooks/README.md) · [evaluation text set](ml/eval/text/README.md) · [recording guide](ml/eval/RECORDING_GUIDE.md) · [results](ml/eval/results/README.md) · [models](ml/models/README.md)

**Code and components:** [prototype app](apps/prototype/README.md) · [Android app](apps/android/README.md) · [hub FHIR server](hub/fhir-server/README.md) · [hub mediator](hub/mediator/README.md) · [hub SMS gateway](hub/sms-gateway/README.md) · [hub indicator engine](hub/indicator-engine/README.md) · [hub database](hub/db/README.md) · [district server](district-server/README.md) · [sync tests](tests/sync/README.md)

**Content and deployment:** [WHO DAK content](content/dak/README.md) · [audio clips](content/audio/README.md) · [branding](apps/prototype/web/branding/README.md) · [data folder](data/README.md) · [hosted app (Hugging Face)](deploy/hf-app/README.md) · [hosted FHIR hub](deploy/hf-fhir/README.md)
