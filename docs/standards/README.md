# Standards and digital public infrastructure

How MaternaSave plugs into a country's digital health systems: the data, terminology and identity standards it uses, and how it fits the World Bank's view of **digital public infrastructure (DPI)**. For the full technical design (tiers, FHIR resource model, sync, security), see the [architecture specification](../architecture/README.md).

## 1. Health data, terminology and identity standards

| Standard | How MaternaSave uses it |
| --- | --- |
| [HL7 FHIR R4](https://hl7.org/fhir/R4/) | Every encounter becomes a transaction Bundle: Patient, EpisodeOfCare, Encounter, Observation, GuidanceResponse, ServiceRequest, Task, Communication, Consent, Provenance, Organization, PractitionerRole, Device. Example: [fhir/examples/referral-bundle.json](../../fhir/examples/referral-bundle.json). **Official HL7 FHIR Validator: 0 errors, 0 warnings** ([result](../../ml/eval/results/fhir-validation.md)); the blood pressure reading passes the FHIR vital-signs BP profile |
| [LOINC](https://loinc.org/) | Blood pressure panel 85354-9, systolic 8480-6, diastolic 8462-4, last menstrual period 8665-2 |
| [UCUM](https://ucum.org/) | Units of measure (mm[Hg], Cel, /min, wk) |
| HL7 terminology | Provenance participant types (verifier, assembler, author), consent scope, data-absent-reason (`asked-unknown` for "Don't know"), confidentiality (`R`, restricted, on partner HIV status) |
| FHIR conditional create (`ifNoneExist`) and `If-Match` | Uploads are safe to retry without duplicates; referral status changes cannot overwrite newer data |
| [OpenHIE architecture](https://guides.ohie.org/arch-spec/architecture-specification/standards-and-profiles.md) | Device → facility hub → national systems design, with a mediator for national exchange (see the architecture document) |
| [World Bank ID4D principles](https://id4d.worldbank.org/principles) | MaternaSave creates its own woman ID and card number; the national ID is optional, consented, never stored as a number and never used as a key or sent by SMS |

## 2. Digital public infrastructure (DPI)

The World Bank describes DPI as foundational digital building blocks for public benefit, most commonly **digital identity, digital payments and trusted data sharing**, built to be interoperable, open, modular, inclusive, user-centric, private and secure by design, and well governed ([*Digital Public Infrastructure and Development: A World Bank Group Approach*, 2025](https://documents1.worldbank.org/curated/en/099031025172027713/pdf/P505739-84c5073b-9d40-4b83-a211-98b2263e87dd.pdf); [World Bank DPI](https://www.worldbank.org/ext/en/topic/digital-and-ai/digital-public-infrastructure-and-services)).

MaternaSave is not itself DPI. It is a **health service built to sit on top of DPI**: it uses a country's identity and data-sharing rails when they exist, and keeps care working when they do not.

| DPI building block | How MaternaSave connects | Where |
| --- | --- | --- |
| **Digital identity** | Issues its own functional woman ID and card code so care never waits for an ID; links to the national foundational ID (e.g. NIN) only with her consent, never storing or keying on the number (the prototype records only that the card was shown; production links through the national ID service's verification token) (World Bank [ID4D principles](https://id4d.worldbank.org/principles)) | [`registry.py`](../../apps/prototype/src/ovamha_proto/registry.py); [architecture section 9](../architecture/README.md) |
| **Trusted data sharing** | Every encounter is an HL7 FHIR R4 Bundle; the facility hub exchanges with national systems only through a mediator (OpenHIE pattern); works with a national health information exchange (mode A), with separate national systems such as an HMIS (mode B), or with none (mode C), and moves between modes without data conversion | [`fhir_bundle.py`](../../apps/prototype/src/ovamha_proto/fhir_bundle.py), [`sync.py`](../../apps/prototype/src/ovamha_proto/sync.py); [architecture section 3.3](../architecture/README.md) |
| **Digital payments** | Not used | — |
| **Messaging rails** | Referral notices and acknowledgements over plain SMS (works on any phone, 2G), with no name or HIV status in the message | [`sms.py`](../../apps/prototype/src/ovamha_proto/sms.py) |

| DPI principle | In MaternaSave |
| --- | --- |
| Interoperable, open standards | FHIR R4, LOINC, UCUM, HL7 terminologies; WHO SMART ANC resource model; official HL7 validator: 0 errors, 0 warnings |
| Modular | A country's guideline is a content file; the danger-sign detector is swappable (`OVAMHA_DETECTOR`); speech models are set per language |
| Inclusive, user-centric | Voice input and read-aloud for workers with low literacy; English, Krio and Yoruba; works offline on a basic phone browser |
| Privacy and security by design | Encryption at rest, audit trail, voice deleted after transcription, data minimisation: [privacy](../privacy/README.md) |
| Governance | Every record carries provenance (who confirmed it, which AI model and which rule produced it) as FHIR Provenance; actions are audited |

## 3. Principles for Digital Development

The World Bank endorsed the [Principles for Digital Development](https://digitalprinciples.org/) in 2015.

| Principle | In MaternaSave |
| --- | --- |
| Design with the user | Built around the health worker's real constraints: no internet, busy clinics, three languages, voice first, keypad for numbers |
| Understand the existing ecosystem | Follows WHO DAK, the national guideline and OpenHIE, so it fits the systems ministries already use |
| Design for scale | Same app for every country; a new country adds a guideline file and language models |
| Build for sustainability | Runs on low-cost hardware with open models; no cloud or per-use AI fees |
| Be data driven | FHIR records are designed to feed national reporting (hub indicator engine, planned); anonymised export for evaluation |
| Use open standards, open data, open source and open innovation | Open standards and open-weight models throughout (see [third-party sources](../../README.md#third-party-sources-and-licences)) |
| Reuse and improve | Reuses WHO DAK and SMART ANC, Whisper, MMS-TTS, MiniLM, HAPI FHIR |
| Address privacy and security | [docs/privacy/README.md](../privacy/README.md) |
| Be collaborative | Clinical content and local-language wording are left for ministries and native-speaker health workers to review |
