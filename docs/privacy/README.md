# Privacy and data protection

What Ovamha does to protect a woman's information, which guidance or law each measure follows, and
where it is in the code. Guidance is layered: **international health guidance** applies everywhere,
**African instruments** set the regional baseline, and **national law** applies where Ovamha is used.
Sierra Leone (the worked example) and Nigeria (Yoruba) are covered. Status is for the prototype in
`apps/prototype` as of 2026-10-04.

| Document | Purpose |
|---|---|
| [voice-data.md](voice-data.md) | Voice recordings are transcribed, then deleted; never stored, never used for training |
| [dpia.md](dpia.md) | Data protection impact assessment (draft), for Sierra Leone and Nigeria |
| [privacy-design-policy.md](privacy-design-policy.md) | Privacy design policy, including retention (draft) |
| [breach-response.md](breach-response.md) | What to do when data is lost, stolen or seen by the wrong person (draft) |

## 1. International health guidance (applies wherever Ovamha is used)

| Ref | Document | What it asks of Ovamha |
|---|---|---|
| **WHO-AI** | WHO, [*Ethics and governance of artificial intelligence for health*](https://iris.who.int/handle/10665/341996), 2021 | Six principles. **P1 protect autonomy**: humans stay in control of medical decisions; informed consent; privacy and confidentiality. P3 transparency, P4 responsibility and accountability, P5 inclusiveness and equity |
| **WHO-DP** | WHO, [*Data principles*](https://www.who.int/data/principles), 2020 | Uphold the right to privacy and the highest standards of data protection; consent is the preferred basis for processing personal data |
| **WHO-DAK** | WHO, *Digital adaptation kit for antenatal care*, 2021: non-functional requirements ANC.NFXNREQ.001-043 (PDF p. 83) | Concrete controls: password access, confidentiality of personal health information, anonymised exports, no remembered credentials, idle logout, encrypted communication, lockout, role-based access, audit logs |
| **ISO 27799** | ISO 27799:2016, *Health informatics: information security management in health using ISO/IEC 27002* | Reference standard for the production hub's security management |

## 2. Africa

| Ref | Instrument | Status for Sierra Leone and Nigeria | What it asks |
|---|---|---|---|
| **ECOWAS** | [Supplementary Act A/SA.1/01/10 on Personal Data Protection within ECOWAS](https://www.statewatch.org/media/documents/news/2013/mar/ecowas-dp-act.pdf), 2010 | **Both are ECOWAS members.** This is the shared regional framework | Health data is sensitive: processing is prohibited (Art. 30) except on listed grounds, e.g. written consent, vital interests, or a public-interest mission of a public authority (Art. 31); principles of consent, fairness, purpose, relevance, limited retention, accuracy, transparency, confidentiality and security (Art. 23-28); right of access, objection, rectification (Art. 39-41); no decision with legal effect based solely on automated processing (Art. 35(2)); transfers outside ECOWAS only with adequate protection (Art. 36); security and confidentiality duties (Art. 42-43); health-data processing needs authorisation from the data protection authority (Art. 12) |
| **AU-M** | African Union, [*Convention on Cyber Security and Personal Data Protection*](https://dataprotection.africa/malabo-convention-set-to-enter-force/) (Malabo Convention), 2014 | In force since 8 June 2023. Neither Sierra Leone nor Nigeria was among the 15 ratifying states then ([EJIL:Talk!](https://www.ejiltalk.org/the-african-unions-malabo-convention-on-cyber-security-and-personal-data-protection-enters-into-force-nearly-after-a-decade-what-does-it-mean-for-data-privacy-in-africa-or-beyond/)); check current status | Continental baseline for data protection principles; followed as good practice |
| **AU-DPF** | African Union, [*Data Policy Framework*](https://fpf.org/blog/the-african-unions-data-policy-framework-context-key-takeaways-and-implications-for-data-protection-on-the-continent/), endorsed Feb 2022 | Policy guidance for all AU members | Privacy by design and by default; health data needs stronger protection and sector-specific governance |

## 3. Country law

### Sierra Leone

| Ref | Document | Status |
|---|---|---|
| **SL-HIS** | Ministry of Health and Sanitation, [*Health Information System Policy*](https://mohs.gov.sl/download/50/policy-documents/17808/his_policy_15-11-2021_final-3.pdf), 2021 | **In force.** Her data is hers (3.5.9(a)); share only with written consent (3.5.9(c)); her right to access (3.5.10(a)); confidentiality and accountability of staff (3.7); security of records (3.6); breach reporting to DMO/MS/DPPI (3.7(c)); research needs SLESRC ethics clearance (3.5.10(d)) |
| **SL-Bill** | [*Data Protection and Right to Access Information Regulatory Commission Bill*, 2025](https://www.dpo-india.com/Resources/privacy_laws_in_africa_nations/Sierra-Leone'Data-Protection-Right-Access-Information-Bill,2025.pdf) | **Not yet law** (national validation concluded 7 Nov 2025, [MoICE](https://moice.gov.sl/moice-concludes-final-national-validation-of-the-data-protection-and-right-to-access-information-bill-2025/)); Sierra Leone has no data protection act today ([Data Protection Africa](https://dataprotection.africa/sierra-leone/)). Followed now; section numbers may change |

### Nigeria

| Ref | Document | Status |
|---|---|---|
| **NG-NDPA** | [*Nigeria Data Protection Act*, 2023](https://www.dataguidance.com/sites/default/files/data_protection_act_2023.pdf), signed 12 June 2023; regulator: Nigeria Data Protection Commission (NDPC); implementation directive [GAID 2025](https://ndpc.gov.ng/wp-content/uploads/2025/07/NDP-ACT-GAID-2025-MARCH-20TH.pdf) | **In force.** Principles (s.24); lawful basis (s.25); notice before collection (s.27); DPIA and consulting the Commission on high risk (s.28); health data is sensitive, allowed for medical care by a professional owing confidentiality (s.30(1)(g)) or public health with safeguards (s.30(1)(h)); children: parental consent, **except for medical care under a duty of confidentiality** (s.31(1), (4)(b)); rights incl. access (s.34), object (s.36), not to be subject to solely automated decisions (s.37); security (s.39); breach notice to the NDPC within 72 hours (s.40(2)); cross-border transfers (s.41-43); registration of controllers of major importance (s.44) |
| **NG-NHA** | *National Health Act*, 2014 ([summary](https://www.mondaq.com/nigeria/healthcare/1340876/legal-considerations-for-electronic-medical-record-systems-in-healthcare-establishment%3Csup%3E1%3Csup%3E----)) | **In force.** All information about a user's health, treatment or stay is confidential (s.26(1)); disclosure only with written consent, court order or law, or a public-health threat (s.26(2)); the head of a facility must prevent unauthorised access to records (s.29); offences include unauthorised access and **re-identifying de-identified records** (s.29) |

Project design: **ARCH** = [Ovamha architecture](../architecture/README.md) (DEV-, DB-, SEC-, ID-, SY- requirements). **ID4D** = World Bank [Principles on Identification](https://id4d.worldbank.org/principles).

## 4. What is in place, and where

| # | Measure | International | Africa | Sierra Leone | Nigeria | Where in the code | Tested in `tests/prototype/` |
|---|---|---|---|---|---|---|---|
| 1 | **Voice recordings deleted** as soon as transcribed, also when transcription fails | WHO-AI P1 | ECOWAS Art. 25(1), (3) | SL-Bill s.26(1)(c)-(d) | NDPA s.24(1)(c)-(d) | `server.py` `_transcribe_upload`; browser copy freed: `app.js` `URL.revokeObjectURL`; ARCH DEV-03 | `test_privacy.py::test_uploaded_audio_is_deleted_after_transcription`, `::test_audio_deleted_even_when_transcription_fails` |
| 2 | **Read-aloud of her details leaves no audio on disk** (transcript, card number, handover: one-off file deleted once sent; leftovers removed at start-up) | WHO-AI P1 | ECOWAS Art. 25(3), 43 | SL-Bill s.26(1)(d) | NDPA s.24(1)(d) | `server.py` `do_speak`, `_start_sync`; `tts.py` `speak(cache=False)` | `::test_read_aloud_of_her_details_leaves_no_audio_on_disk` |
| 3 | **Voice and patient data never used for training** | WHO-AI P1, P4; WHO-DP | ECOWAS Art. 25(1) | SL-Bill s.27(1), s.39(1) | NDPA s.24(1)(b) | [voice-data.md](voice-data.md); training reads only public data and our own text: `ml/textclf/train.py`, Kaggle notebook | `::test_training_code_never_reads_app_data` |
| 4 | **Encryption at rest** of registry, SMS log, sync outbox, audit log; owner-only files | WHO-DAK .002 | ECOWAS Art. 28, 43 | SL-HIS 3.6(c); SL-Bill s.55(4)(c) | NDPA s.24(2), s.39; NHA s.29 | `secure_store.py` (used by `registry.py`, `sms.py`, `sync.py`, `audit.py`); ARCH DEV-02, DB-02 | `::test_registry_is_encrypted_on_disk`, `::test_sms_log_and_outbox_are_encrypted`, `::test_plain_registry_from_older_version_is_read_then_encrypted` |
| 5 | **Audit trail** of sign-ins, failures, lockouts, idle sign-out, record created/opened/shown, notice, encounter, SMS, FHIR exchange, export; identifiers only | WHO-DAK .016-.021; WHO-AI P4 | ECOWAS Art. 42 | SL-HIS 3.9(a)-(b) | NDPA s.24(3) (accountability); NHA s.29 | `audit.py`; calls in `server.py`, `sync.py`, `scripts/export_anonymised.py`; ARCH SEC-06 | `::test_audit_trail_through_the_api`, `::test_audit_refuses_personal_details` |
| 6 | **Automatic sign-out** after 15 min without use and after an 8-hour shift | WHO-DAK .006 | ECOWAS Art. 43 | SL-HIS 3.5.2(c) | NHA s.29 | `server.py` `visit`, `IDLE_SECONDS`, `MAX_SESSION_SECONDS` | `::test_idle_sign_out`, `::test_sign_in_ends_after_one_shift` |
| 7 | **PIN never remembered by the browser**; "stay signed in" limited to the shift | WHO-DAK .005 | | | | `app.js` sign-in form (`autocomplete="off"`) | `::test_pin_field_not_remembered_by_browser` |
| 8 | **PIN access, lockout** after 5 wrong PINs; salted PBKDF2 hashes; same message for unknown user or wrong PIN | WHO-DAK .001, .013 | ECOWAS Art. 43 | SL-HIS 3.6(c) | NHA s.29 | `auth.py` | `test_auth.py` |
| 9 | **Privacy notice read to her** before registration; registration refused without it; time recorded | WHO-AI P1 (informed); WHO-DP | ECOWAS Art. 27 | SL-Bill s.27(3); SL-HIS 3.5.9 | NDPA s.27 | `app.js` `PRIVACY_NOTICE`; `server.py` `RegisterIn.notice_given`; `registry.py` `register`, `privacy_notice_at`; `content/readback/phrases.json` `privacy_notice` | `::test_registration_needs_privacy_notice` |
| 10 | **She can see her record** ("Show record", printable, audited) | WHO-AI P1 | ECOWAS Art. 39 | SL-HIS 3.5.9(a), 3.5.10(a); SL-Bill s.43 | NDPA s.34 | `server.py` `/api/woman/record`; `registry.py` `her_record`; `app.js` `showRecord` | `::test_she_can_see_her_record` |
| 11 | **Anonymised export**: no names, phones, card code, IDs, exact dates or free text; random per-export pseudonym; age bands | WHO-DAK .004 | ECOWAS Art. 25(4) | SL-Bill s.36(2), s.39(3)(i) | NDPA s.24(1)(c); NHA s.29 (re-identifying is an offence) | `scripts/export_anonymised.py` | `::test_anonymised_export_drops_identifiers` |
| 12 | **National ID optional and consented**; number never stored; care never depends on it | ID4D | ECOWAS Art. 25(2) | SL-HIS 2.5(f) | NDPA s.24(1)(c) | `registry.py` `register`; ARCH ID-03, AP-06 | `test_registry.py` |
| 13 | **Consent to referral** recorded, refusal included, before any referral SMS | WHO-AI P1 | ECOWAS Art. 31(2) | SL-HIS 3.5.9(c), 3.7(b) | NHA s.26(2) | `server.py` `/api/referral/complete` | `test_server.py` |
| 14 | **The worker decides**: every AI suggestion needs confirmation; rules advise, the worker refers | WHO-AI P1 (humans in control), P4 | ECOWAS Art. 35(2) | SL-Bill s.46 | NDPA s.37 | `confirm.py`; `detect.py`; [decision record](../decisions/guideline-advice-not-fine-tuning.md) | `test_pipeline.py`, `test_detect.py` |
| 15 | **AI runs on the device** (speech recognition, text classifier); nothing sent to an outside service | WHO-AI P1 | ECOWAS Art. 36 | SL-Bill s.41 | NDPA s.41-43 | `asr.py`, `classifier.py` | — |
| 16 | **Hosted demo warns**: fictional data only, "Do not enter real patient information", runs outside the country | | ECOWAS Art. 36 | SL-Bill s.41 | NDPA s.41-43 | `app.js` `showHostedNotice` | — |
| 17 | **No clinical data cached by the installed app** | WHO-DAK .002 | ECOWAS Art. 42 | SL-HIS 3.5.2(b) | NHA s.26(1) | `web/sw.js` | — |

Run the privacy tests: `.venv/bin/pytest tests/prototype/test_privacy.py -v`

## 5. Lawful basis for processing her health data

| | Basis for care | Children (pregnant adolescents) | Regulator to notify / register with |
|---|---|---|---|
| **ECOWAS** | Written consent, vital interests, or a public-interest mission of a public authority (Art. 31(2), (3), (9)) | Not specific | National data protection authority; health data needs its authorisation (Art. 12) |
| **Sierra Leone** | SL-Bill: medical purposes by a health professional or someone with an equivalent duty of confidentiality (s.35(1)(b)(iv)); share only with written consent (SL-HIS 3.5.9(c)) | SL-Bill s.34: parental consent. **Open question** for confidential adolescent care | No authority yet; once enacted, register (s.49) and submit the DPIA where high risk remains (s.33(3)) |
| **Nigeria** | Medical care by a professional owing confidentiality (NDPA s.30(1)(g)); disclosure only as NHA s.26(2) allows | Parental consent **not needed** for medical care under a duty of confidentiality (NDPA s.31(4)(b)) | NDPC: consult on a high-risk DPIA (s.28); register if a controller of major importance (s.44); breach within 72 hours (s.40(2)) |

## 6. Not done in the prototype (needed before real use)

| Requirement | Follows | Plan |
|---|---|---|
| Device key in hardware (Android Keystore) and the FHIR SDK's encrypted database; remote wipe | WHO-DAK .002; NDPA s.39; ARCH DEV-02, SEC-01 | Android app. The prototype's key file sits next to the data (see `secure_store.py`) |
| Encrypted transport (TLS) device to hub, hub to national systems | WHO-DAK .007; ECOWAS Art. 28 | `make run-https` uses a self-signed certificate for testing only |
| Role-based access, user management, password change and reset by an admin | WHO-DAK .008-.015, .024-.032 | Hub (Keycloak) |
| Audit as FHIR AuditEvent on the hub; security management to ISO 27799 | ARCH SEC-06; ISO 27799 | Hub |
| Retention periods and deletion of records | ECOWAS Art. 25(3), 44; NDPA s.24(1)(d); SL-Bill s.40 | National retention schedules needed; see [privacy-design-policy.md](privacy-design-policy.md) |
| Correction, erasure and restriction requests | ECOWAS Art. 41; NDPA s.34; SL-Bill s.28, s.42 | Process in the policy; screens later |
| Regulator steps: NDPC consultation/registration (Nigeria); Commission registration and DPIA (Sierra Leone, once enacted); ECOWAS Art. 12 authorisation | See section 5 | Before deployment in each country |
| Krio and Yoruba privacy notice | ECOWAS Art. 27; NDPA s.27; SL-Bill s.27(3) | Native-speaker health workers (empty in `phrases.json`) |
| Ethics approval before recording or field testing with people | SL-HIS 3.5.10(d); Nigerian national/state health research ethics committees | See [voice-data.md](voice-data.md) |
| AfriSpeech-200 data is CC BY-NC-SA 4.0 (non-commercial) | Licence | Retrain without it before any commercial use |
