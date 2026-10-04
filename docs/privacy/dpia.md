# Data protection impact assessment (DPIA): Ovamha

**Status: DRAFT for review**, 2026-10-04. Prepared for the project team; not yet reviewed by the
Ministry of Health, a data protection specialist or clinicians.

**Why a DPIA:** Ovamha processes health data about pregnant women, including adolescents, which is
sensitive personal data under the draft *Data Protection and Right to Access Information Regulatory
Commission Bill, 2025* (s.1 "sensitive personal data"; s.29). Processing likely to result in high risk
needs a DPIA before processing starts (s.33(1)), which must be submitted to the Commission at least
60 days before processing where high risk remains (s.33(3)). The Bill is not yet law; this DPIA
follows its structure (s.33(2)(a)-(d)) so it is ready when the law passes.

Sources are listed at the end. Section references: **Bill** = draft Bill 2025; **HIS** = MoHS
Health Information System Policy 2021; **DAK** = WHO ANC Digital Adaptation Kit 2021;
**ARCH** = [Ovamha architecture](../architecture/README.md).

## 1. Description of the processing (s.33(2)(a))

**Purpose.** Help community health workers, nurses and midwives at health posts in Sierra Leone
spot danger signs in pregnancy early, follow WHO antenatal guidance and refer women quickly.

**Controller.** To be confirmed: the facility / District Health Management Team running Ovamha,
under the Ministry of Health and Sanitation. The Ovamha project is the developer (processor role
for support only, if any).

**People whose data is processed.** Pregnant women attending antenatal care (some under 18);
health workers (users); a woman's alternative contact, if she gives one.

**Data.**

| Category | Examples | Where |
|---|---|---|
| Identification | Ovamha woman ID (random), card code, name, address, phone, alternative contact | Phone/hub registry (encrypted) |
| Health | Symptoms, danger signs, measurements (BP, pulse, temperature), pregnancy history, medications, HIV partner status, substance use | Encounter, hub FHIR store |
| National ID | Only that a card was shown, with consent; never the number | Registry |
| Voice | Health worker's spoken description | Memory and a temporary file only; deleted after transcription ([voice-data.md](voice-data.md)) |
| Referral | SMS to the receiving facility (encounter code, danger signs), replies | SMS log (encrypted), FHIR Communication |
| Users and audit | Worker ID, sign-in times, actions (no health details) | Audit log (encrypted) |

**Flow.** Phone (offline) → facility hub over local Wi-Fi → national systems through the hub
mediator only (ARCH AP-05). Speech recognition and danger-sign detection run on the device or hub;
nothing is sent to an outside AI service.

**Lawful basis.** Care: processing for medical purposes by health professionals or people with an
equivalent duty of confidentiality (Bill s.35(1)(b)(iv)); vital interests in an emergency
(s.35(1)(b)(ii)). Sharing with third parties beyond care: her written consent (HIS 3.5.9(c)).
National ID link: her consent (ARCH ID-03). SMS reminders: her consent (registration question
`wants_reminders`). Notice at collection: Bill s.27(3).

**Retention.** Encounter workspace (transcripts, proposals, audio): deleted when the encounter closes
(ARCH DEV-03). Health records: per Ministry of Health retention schedule (to be obtained; Bill s.40,
HIS 3.6(a)). SMS bodies: purged after a configurable period (ARCH DB-07).

## 2. Necessity and proportionality (s.33(2)(b))

| Question | Answer |
|---|---|
| Is each data item needed? | Fields follow the WHO ANC DAK data dictionary (ANC.A4, ANC.B5-B8). National ID is optional and never stored as a number. Registration details beyond name are optional. |
| Could less identifying data work? | Care needs the woman to be found again: a random card code, not her national ID, is the key (ARCH AP-06; HIS 2.5(f)). Reporting uses the anonymised export (`scripts/export_anonymised.py`). |
| Is voice necessary? | Voice makes recording fast for workers with low literacy or busy clinics; typing is always possible. Voice is kept for seconds only. |
| Is AI necessary, and is it proportionate? | AI only proposes; the worker confirms every item and decides on referral (Bill s.46). |
| Does she know? | Privacy notice read before registration (Bill s.27(3)); she can see her record (HIS 3.5.10(a); Bill s.43). |

## 3. Risks to the people concerned (s.33(2)(c))

Likelihood and severity: L = low, M = medium, H = high, before and after the measures in section 4.

| # | Risk | Harm | Before | After |
|---|---|---|---|---|
| R1 | Lost or stolen phone exposes records | Disclosure of pregnancy, HIV status, adolescent pregnancy; stigma, violence | H/H | L/H (encryption, auto sign-out; remote wipe planned) |
| R2 | Another person uses a worker's unlocked session | Unauthorised viewing or changes | M/H | L/M (15-min idle sign-out, shift limit, audit) |
| R3 | Voice recordings kept or leaked | Her words and voice of the worker disclosed | M/H | L/M (deleted after transcription; no read-aloud cache of her details) |
| R4 | SMS read by the wrong person (shared phones at the receiving facility) | Disclosure | M/M | M/M (minimal SMS content: code and danger signs; no name). Review with MoHS |
| R5 | AI misses a danger sign or proposes a wrong one | Delayed referral or unnecessary referral | M/H | M/H (worker confirms; safety-net flags; rules from WHO DAK; measured recall reported). Clinical safety review needed |
| R6 | Data used for something else (research, commercial, training) | Loss of control; consent breached | M/M | L/M (purpose limitation; voice never trained on; anonymised export; ethics approval required, HIS 3.5.10(d)) |
| R7 | Data processed outside Sierra Leone | Weaker protection | M/M | L/M (on-device AI; hosted demo fictional only; Bill s.41) |
| R8 | Inaccurate record (speech recognition error) | Wrong care | M/H | L/M (read-back, confirmation, worker correction; her right to correction, Bill s.42) |
| R9 | Re-identification from exports in small communities | Disclosure | M/M | L/M (no names, dates or IDs; age bands; review counts under 5) |
| R10 | Adolescents: consent and confidentiality | Harm to a child; family disclosure | M/H | M/H (Bill s.34 parental consent conflicts with confidential adolescent care; needs MoHS guidance) |
| R11 | Insider misuse by staff | Disclosure, discrimination | M/H | L/H (audit of record access, HIS 3.7(b) accountability; role-based access planned) |

## 4. Measures to address the risks (s.33(2)(d))

Implemented and tested in the prototype (details and code locations in [README.md](README.md)):
voice deleted after transcription; no read-aloud audio of her details on disk; encryption at rest
of registry, SMS log, outbox and audit; owner-only files; audit trail without personal details;
15-minute idle and 8-hour shift sign-out; PIN not remembered; lockout after 5 wrong PINs; privacy
notice before registration; "Show her record"; anonymised export; national ID never stored;
consent to referral; worker confirms all AI output; on-device AI; no clinical data in the app cache;
hosted-demo warning.

Planned before field use: hardware-backed keys and the FHIR SDK encrypted database; remote wipe;
TLS on every link; role-based access and admin user management; audit as FHIR AuditEvent on the hub;
retention schedule; correction and erasure process; Krio and Yoruba notices by native speakers;
staff confidentiality training; ethics approval for any study; breach response drills
([breach-response.md](breach-response.md)).

## 5. Remaining high risks and decisions needed

1. **Adolescents (R10)**: how to reconcile parental consent (Bill s.34) with confidential antenatal
   care for girls under 18. Needs Ministry of Health and legal guidance.
2. **Clinical safety (R5)**: the AI's danger-sign recall must be measured on real recordings in
   Krio and Yoruba before use; until then, the worker's own assessment is primary.
3. **Retention schedule**: obtain the national health-records retention periods.
4. **SMS content (R4)**: agree the minimum content with receiving facilities.

## 6. Review

Review this DPIA before any pilot, after any change to the data collected or where it goes, and at
least yearly. Record reviewer, date and changes below.

| Date | Reviewer | Change |
|---|---|---|
| 2026-10-04 | Ovamha project (draft) | First draft |

## Sources

- *The Data Protection and Right to Access Information Regulatory Commission Act, 2025* (Bill, not yet law): s.1, s.26, s.27, s.29, s.33, s.34, s.35, s.37, s.39, s.40, s.41, s.42, s.43, s.46. [PDF](https://www.dpo-india.com/Resources/privacy_laws_in_africa_nations/Sierra-Leone'Data-Protection-Right-Access-Information-Bill,2025.pdf)
- MoHS Sierra Leone, *Health Information System Policy*, 2021: s.2.5(e)-(f), 3.5.2, 3.5.9, 3.5.10, 3.6, 3.7, 3.9. [PDF](https://mohs.gov.sl/download/50/policy-documents/17808/his_policy_15-11-2021_final-3.pdf)
- WHO, *Digital adaptation kit for antenatal care*, 2021: data dictionary ANC.A4, ANC.B5-B8; non-functional requirements ANC.NFXNREQ.001-043.
- World Bank ID4D, *Principles on Identification for Sustainable Development*.
- Ovamha architecture (AP-05, AP-06, DEV-02, DEV-03, DB-02, DB-07, ID-03, SEC-01, SEC-02, SEC-06).
