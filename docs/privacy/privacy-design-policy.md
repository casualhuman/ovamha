# Privacy design policy: MaternaSave

**Status: DRAFT**, 2026-10-04. One policy for every country where MaternaSave runs, built on
international health guidance (WHO *Ethics and governance of AI for health* 2021; WHO *Data
principles* 2020; WHO ANC DAK ANC.NFXNREQ) and the African baseline (ECOWAS Supplementary Act
A/SA.1/01/10; AU Data Policy Framework 2022: privacy by design and by default). Country rules:
**Nigeria**: Data Protection Act 2023 (privacy by design: s.24(2), s.39; notice: s.27) and National
Health Act 2014 (s.26, s.29). **Sierra Leone**: MoHS Health Information System Policy 2021, and the
draft Data Protection Bill 2025, whose s.54 sets this policy's structure; once enacted it must be
approved by the Commission and published (s.54(2)-(4)). Abbreviations as in [README.md](README.md);
unprefixed "Bill" and "HIS" mean the Sierra Leone texts.

## 1. Practices that anticipate and avoid harm (s.54(1)(a))

- **Collect only what care needs** (Bill s.26(1)(c), s.27(2)): fields follow the WHO ANC DAK data
  dictionary; national ID is optional and its number is never stored; most registration details are
  optional.
- **Tell her first** (Bill s.27(3)): the worker reads the privacy notice before registering a woman.
  MaternaSave refuses to register without it and records when it was read.
- **Her data is hers** (HIS 3.5.9(a)): she can see her record ("Show record", printable) (HIS
  3.5.10(a); Bill s.43) and ask for corrections (Bill s.42).
- **Share only for her care, or with her written consent** (HIS 3.5.9(c), 3.7(b)): referral data goes
  to the receiving facility after her consent to referral is recorded.
- **People decide, not the software** (Bill s.46): AI output is a proposal until the worker confirms it.
- **Purpose limitation** (Bill s.27(1), s.39): data collected for care is not used for anything else;
  voice is never used for training ([voice-data.md](voice-data.md)); research needs SLESRC ethical
  clearance (HIS 3.5.10(d)).
- **Accountability** (HIS 3.7(b), Bill s.26(1)(a)): every sign-in, record access and data exchange is
  audited.

## 2. Technology (s.54(1)(b))

| Control | Standard | Prototype | Production |
|---|---|---|---|
| Encryption at rest | AES (Fernet: AES-128-CBC + HMAC-SHA256) | `secure_store.py` | Android FHIR SDK encrypted database, key in Android Keystore |
| Encryption in transit | TLS 1.2+ | Self-signed HTTPS for testing | TLS on device-hub and hub-national links (ARCH SEC-02) |
| Authentication | Salted PBKDF2-SHA256 PINs, lockout | `auth.py` | Plus role-based access, admin user management (DAK NFXNREQ.008-032) |
| Session control | Idle sign-out 15 min, shift limit 8 h | `server.py` `visit` | Same, plus device screen lock |
| Audit | Append-only, identifiers only | `audit.py` | FHIR AuditEvent, IHE BALP (ARCH SEC-06) |
| Identity | Random woman ID + card code with check character | `registry.py` | Linked to national ID only with consent (ID4D) |
| AI | On-device speech recognition and text classifier | `asr.py`, `classifier.py` | Same |
| Data exchange | FHIR R4, through the hub mediator only | `fhir_bundle.py`, `sync.py` | ARCH AP-05 |

## 3. Legitimate interests and innovation without compromising privacy (s.54(1)(c))

Faster, safer antenatal care: voice entry for busy health workers and danger-sign detection to
speed up referral. Innovation is kept on the device, and models are trained only on public or
consented data, never on patient records or recordings.

## 4. Obligations (s.54(1)(d))

| Who | Obligation |
|---|---|
| Controller (Sierra Leone: facility / DHMT under MoHS; Nigeria: the health facility or state ministry; to be confirmed) | Approve this policy and the [DPIA](dpia.md); respond to her requests (ECOWAS Art. 39-41; NDPA s.34-36; SL-Bill s.28, 42, 43); report breaches ([breach-response.md](breach-response.md)); Nigeria: NDPC consultation and registration where required (NDPA s.28, s.44); Sierra Leone: register once the Bill is enacted (s.49) |
| Health workers | Keep information confidential (SL-HIS 3.7(b); NHA s.26(1)); read the privacy notice; never share PINs or devices while signed in; report lost devices and suspected breaches immediately (SL-HIS 3.7(c)) |
| MaternaSave developers | Build privacy in by default (Bill s.55); keep the controls in [README.md](README.md) tested; never use patient data or recordings for development or training |

## 5. Privacy from collection to deletion (s.54(1)(e))

| Data | Kept | Then |
|---|---|---|
| Voice recording | Until transcribed (seconds) | Deleted (`server.py` `_transcribe_upload`) |
| Read-aloud audio of her details | Until played | Deleted (`server.py` `do_speak`) |
| Transcript, AI proposals, unconfirmed items | Until the encounter closes | Discarded (ARCH DEV-03; `confirm.py` `finalise`) |
| Registry on the phone | While she is in care at the facility | Per the national retention schedule (to be obtained for each country; ECOWAS Art. 25(3), 44; NDPA s.24(1)(d)) |
| Sync outbox | Until uploaded to the hub | Deleted after upload (`sync.py` `flush`) |
| Hub health records | Per national health-records retention policy (ARCH DB-07; HIS 3.6(a)) | Deleted or de-identified at the end of the period (Bill s.40(4)) |
| SMS bodies | Configurable period (ARCH DB-07) | Purged; the FHIR Communication remains |
| Audit log | Per national policy (needed to answer access requests, Bill s.40(3)(b)) | Archived |
| Anonymised exports | As needed for the report | Not personal data, but review small counts before sharing |

**Test and demo data:** only fictional women. The hosted demo shows "Do not enter real patient
information". Local test data lives in `OVAMHA_DATA` and can be wiped by deleting that folder.

## Sources

- WHO, *Ethics and governance of artificial intelligence for health*, 2021; WHO, *Data principles*, 2020.
- ECOWAS, *Supplementary Act A/SA.1/01/10*, 2010: Art. 23-28, 36, 39-44. African Union, *Data Policy Framework*, 2022.
- *Nigeria Data Protection Act*, 2023: s.24, 27, 28, 34-36, 39, 44. *National Health Act* (Nigeria), 2014: s.26, s.29.
- *The Data Protection and Right to Access Information Regulatory Commission Act, 2025* (Sierra Leone Bill, not yet law): s.26-28, 39-43, 46, 49, 54, 55.
- MoHS Sierra Leone, *Health Information System Policy*, 2021: s.3.5.9, 3.5.10, 3.6, 3.7.
- WHO, *Digital adaptation kit for antenatal care*, 2021: ANC.NFXNREQ.001-043.
- MaternaSave architecture: AP-05, DEV-03, DB-07, SEC-02, SEC-06.
