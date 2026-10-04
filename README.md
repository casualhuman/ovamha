# Ovamha: offline voice guidance for safer maternal care

Ovamha (Offline Voice Assistant for Maternal Healthcare in Africa) helps community health workers, nurses and midwives in Sierra Leone and Nigeria assess a pregnant woman by voice, with no internet. The worker describes the situation; Ovamha writes down what it understood, reads it back for confirmation, checks the confirmed facts against WHO and Sierra Leone guidelines, and **suggests** what to do. **The health worker decides.** If she refers, Ovamha walks her through the national referral pathway and prepares the referral SMS, the FHIR record and a printable referral letter.

> Prototype for the World Bank Small AI for Development Hackathon (October 2026). Full documentation in progress.

## Run it

```
make setup     # once: Python environment and packages
make test      # 140 automated tests
make run       # open http://localhost:8000
```

Phone on the same Wi-Fi: `make run-https` (microphones need HTTPS).

## For judges: demo logins

Fictional demo accounts, checked offline on the device (PINs are stored only as salted hashes).

| Health worker | Username | PIN |
| --- | --- | --- |
| Nurse Fati (Sierra Leone) | `fati` | `769131` |
| CHW Aminata (Sierra Leone) | `aminata` | `507892` |
| Midwife Funmi (Nigeria) | `funmi` | `186706` |

Try: sign in as `fati` → **Guide me** → **First visit** → describe *"She is 28 weeks pregnant, she has seen blood since this morning, a lot of it. She fainted yesterday but she is fine now. No fever."* → confirm → **Check the guidelines** → decide → referral letter.

## What works now (all offline)

- Offline sign-in (username + PIN, hashed on the device)
- Registration per WHO ANC DAK ANC.A4; national ID asked first, consented, number never stored; card number with a check character
- First-contact history per ANC.B6, only when no danger sign is present
- Voice description, speech recognition (Whisper small), extraction and an add-only AI safety net; every item confirmed by the worker
- Numbers by keypad or voice; read-aloud in English, Krio and Yoruba voices (MMS-TTS)
- Guideline advice with citations: WHO ANC DAK (demo rules) and the Sierra Leone Integrated Obstetric and Newborn Care Guideline (2026 draft); the worker decides
- Referral pathway: consent, pre-referral checklist, iSBAR call script, simulated SMS, printable referral letter with feedback slip
- HL7 FHIR R4 records (validated structurally), device outbox that syncs to a hub FHIR server when reachable

## Honest limits

- Krio and Yoruba speech recognition and read-back wording still need native-speaker data
- Danger-sign codes are placeholders until the DAK annexes are extracted
- SMS is simulated without a GSM modem; the hub server needs Docker
- No measured accuracy yet: evaluation protocol in [ml/eval/](ml/eval/)

## Key documents

- [docs/architecture/README.md](docs/architecture/README.md): **backend architecture specification** (tiers, FHIR resource model, identity, sync, SMS, security, AI provenance)
- [docs/decisions/agent-handover.md](docs/decisions/agent-handover.md): project brief and design decisions
- [docs/decisions/dak-first-contact.md](docs/decisions/dak-first-contact.md): alignment with the WHO ANC DAK
- [docs/decisions/guideline-advice-not-fine-tuning.md](docs/decisions/guideline-advice-not-fine-tuning.md): why guideline rules, and why the worker decides
