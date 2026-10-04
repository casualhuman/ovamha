# Privacy and data protection

What Ovamha does to protect a woman's information, which rule each measure follows, and where it
is in the code. Status is for the prototype in `apps/prototype` as of 2026-10-04.

Documents in this folder:

| Document | Purpose |
|---|---|
| [voice-data.md](voice-data.md) | Voice recordings are transcribed, then deleted; never stored, never used for training |
| [dpia.md](dpia.md) | Data protection impact assessment (draft) |
| [privacy-design-policy.md](privacy-design-policy.md) | Privacy design policy, including retention (draft) |
| [breach-response.md](breach-response.md) | What to do when data is lost, stolen or seen by the wrong person (draft) |

## Sources

| Ref | Document | Status |
|---|---|---|
| **HIS** | Ministry of Health and Sanitation, Sierra Leone. *Health Information System Policy*, 15 Nov 2021. [PDF](https://mohs.gov.sl/download/50/policy-documents/17808/his_policy_15-11-2021_final-3.pdf) | In force |
| **Bill** | *The Data Protection and Right to Access Information Regulatory Commission Act, 2025* (Bill). [PDF](https://www.dpo-india.com/Resources/privacy_laws_in_africa_nations/Sierra-Leone'Data-Protection-Right-Access-Information-Bill,2025.pdf); national validation concluded 7 Nov 2025 ([MoICE](https://moice.gov.sl/moice-concludes-final-national-validation-of-the-data-protection-and-right-to-access-information-bill-2025/)) | **Not yet law.** Sierra Leone has no data protection act today ([Data Protection Africa](https://dataprotection.africa/sierra-leone/)). Followed now so Ovamha is ready when it passes; section numbers may change |
| **DAK** | WHO. *Digital adaptation kit for antenatal care*, 2021. Non-functional requirements ANC.NFXNREQ.001-043 (PDF p. 83) | WHO guidance |
| **ARCH** | Ovamha [architecture](../architecture/README.md): DEV-, DB-, SEC-, ID-, SY- requirements | Project design |
| **ID4D** | World Bank, [Principles on Identification](https://id4d.worldbank.org/principles) | Guidance (identity) |

## What is in place, and where

| # | Measure | Follows | Where in the code | Tested in |
|---|---|---|---|---|
| 1 | **Voice recordings deleted** as soon as they are transcribed, even when transcription fails | ARCH DEV-03; Bill s.26(1)(c)-(d) (no more than necessary, kept no longer than needed) | `server.py` `_transcribe_upload`; browser recording freed: `app.js` `URL.revokeObjectURL` | `test_privacy.py::test_uploaded_audio_is_deleted_after_transcription`, `::test_audio_deleted_even_when_transcription_fails` |
| 2 | **Read-aloud of her details leaves no audio on disk** (her transcript, card number and handover are synthesised to a one-off file, deleted once sent; leftovers removed at start-up) | ARCH DEV-03 | `server.py` `do_speak` (`personal`), `tts.py` `speak(cache=False)`, `server.py` `_start_sync` | `::test_read_aloud_of_her_details_leaves_no_audio_on_disk` |
| 3 | **Voice and patient data never used for training** | Bill s.27(1), s.39(1) (use only for the purpose collected); speaker consent in `ml/eval/RECORDING_GUIDE.md` | See [voice-data.md](voice-data.md); training code reads only public data and our own template text: `ml/textclf/train.py`, Kaggle notebook | `::test_training_code_never_reads_app_data` |
| 4 | **Encryption at rest** of the woman registry, SMS log (phone numbers, message text), sync outbox (FHIR bundles) and audit log; owner-only files and folder | DAK NFXNREQ.002; HIS 3.6(c); Bill s.55(4)(c); ARCH DEV-02, DB-02, SEC-01 | `secure_store.py` (used by `registry.py` `_load/_save`, `sms.py` `_log`, `sync.py`, `audit.py`) | `::test_registry_is_encrypted_on_disk`, `::test_sms_log_and_outbox_are_encrypted`, `::test_plain_registry_from_older_version_is_read_then_encrypted` |
| 5 | **Audit trail**: sign-in, sign-out, failed and locked sign-ins, idle sign-out, record created, opened and shown to her, privacy notice, encounter finished, SMS sent and received, FHIR upload and failure, anonymised export. Identifiers only; refuses names, phone numbers, transcripts | DAK NFXNREQ.016-021; HIS 3.9(a)-(b); ARCH SEC-06, SY-07 | `audit.py`; calls in `server.py`, `sync.py`, `scripts/export_anonymised.py` | `::test_audit_trail_through_the_api`, `::test_audit_refuses_personal_details` |
| 6 | **Automatic sign-out** after 15 minutes without use (`OVAMHA_IDLE_MINUTES`), and after one 8-hour shift (`OVAMHA_SESSION_HOURS`) | DAK NFXNREQ.006 | `server.py` `visit`, `IDLE_SECONDS`, `MAX_SESSION_SECONDS` | `::test_idle_sign_out`, `::test_sign_in_ends_after_one_shift` |
| 7 | **PIN never remembered by the browser**; "stay signed in" limited to the shift and still signs out when idle | DAK NFXNREQ.005 | `app.js` sign-in form (`autocomplete="off"`) | `::test_pin_field_not_remembered_by_browser` |
| 8 | **Password-protected access, lockout** after 5 wrong PINs for 5 minutes; same message for unknown user or wrong PIN; PINs stored as salted PBKDF2 hashes | DAK NFXNREQ.001, .013 | `auth.py` | `test_auth.py` |
| 9 | **Privacy notice read to her** before registration (what is collected, why, who receives it, recording deleted, right to see her record, care is the same if she declines); registration refused without it; time recorded | Bill s.27(3); HIS 3.5.9, 3.5.10 | `app.js` `PRIVACY_NOTICE`, registration card; `server.py` `RegisterIn.notice_given`; `registry.py` `register`, `privacy_notice_at`; read-aloud `content/readback/phrases.json` `privacy_notice` | `::test_registration_needs_privacy_notice` |
| 10 | **She can see her record**: "Show her record" on her card, printable; opening it is audited | HIS 3.5.9(a) (her data is hers), 3.5.10(a); Bill s.43, s.47 | `server.py` `/api/woman/record`; `registry.py` `her_record`; `app.js` `showRecord` | `::test_she_can_see_her_record` |
| 11 | **Anonymised export** for reporting and evaluation: no names, phone numbers, card code, IDs, exact dates or free text; random per-export pseudonym; 5-year age bands | DAK NFXNREQ.004; Bill s.36(2), s.39(3)(i) | `scripts/export_anonymised.py` | `::test_anonymised_export_drops_identifiers` |
| 12 | **National ID optional and consented**; number never stored; care never depends on it | ID4D; HIS 2.5(f) (health ID not linked to national ID); ARCH ID-03, AP-06 | `registry.py` `register` | `test_registry.py` |
| 13 | **Consent to referral** recorded, refusal included, before any referral SMS | HIS 3.5.9(c), 3.7(b) | `server.py` `/api/referral/complete` | `test_server.py` |
| 14 | **The worker decides**: every AI suggestion needs the worker's confirmation; rules advise, the worker refers | Bill s.46 (no decision based solely on automated processing) | `confirm.py`; `detect.py`; [decision record](../decisions/guideline-advice-not-fine-tuning.md) | `test_pipeline.py`, `test_detect.py` |
| 15 | **AI runs on the device** (speech recognition, text classifier): no audio or text sent to an outside service | Bill s.41 (processing outside Sierra Leone) | `asr.py`, `classifier.py` | — |
| 16 | **Hosted demo warns**: fictional data only, "Do not enter real patient information", runs outside Sierra Leone | Bill s.41 | `app.js` `showHostedNotice` | — |
| 17 | **No clinical data cached by the installed app** (service worker skips `/api/`) | HIS 3.5.2(b) | `web/sw.js` | — |

Run the privacy tests: `.venv/bin/pytest tests/prototype/test_privacy.py -v`

## Not done in the prototype (needed before real use)

| Requirement | Follows | Plan |
|---|---|---|
| Device key in hardware (Android Keystore) and the FHIR SDK's encrypted database; remote wipe | ARCH DEV-02, SEC-01 | Android app. The prototype's key file sits next to the data (see `secure_store.py`) |
| Encrypted transport (TLS) device to hub, hub to national systems | DAK NFXNREQ.007; ARCH SEC-02 | `make run-https` uses a self-signed certificate for testing only |
| Role-based access, user management, password change and reset by an admin | DAK NFXNREQ.008-015, .024-032 | Hub (Keycloak) |
| Audit as FHIR AuditEvent on the hub, with synchronised clocks | ARCH SEC-06 | Hub |
| Retention periods and deletion of records | Bill s.40; HIS 3.6(a); ARCH DB-07 | Ministry of Health retention schedule needed; see [privacy-design-policy.md](privacy-design-policy.md) |
| Correction, erasure and restriction requests | Bill s.28, s.42 | Process in the policy; screens later |
| Registration with the Data Protection Commission, approved privacy design policy, DPIA submitted | Bill s.33, s.49, s.54 | When the Bill is enacted and the Commission exists |
| Krio and Yoruba privacy notice | Bill s.27(3) | Must be written by native-speaker health workers (empty in `phrases.json`) |
| Ethics approval before recording or field testing with people | HIS 3.5.10(d) | See [voice-data.md](voice-data.md) |
| AfriSpeech-200 data is CC BY-NC-SA 4.0 (non-commercial) | Licence | Retrain without it before any commercial use |
