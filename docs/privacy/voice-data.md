# Voice data: transcribed, then deleted, never used for training

**Short version:** when a health worker speaks to Ovamha, the recording exists only long enough
to be turned into text. It is then deleted. Recordings are never stored, never sent to an outside
service, and never used to train or improve any model.

## What happens to a recording

| Step | What happens | Where in the code |
|---|---|---|
| 1. Record | The browser records into memory (no file is saved on the phone) | `apps/prototype/web/app.js` `startRecorder` |
| 2. Replay | The worker may replay it to check it; the in-memory copy is freed when she records again, starts a new check or signs out | `app.js` `URL.revokeObjectURL` |
| 3. Transcribe | The recording is sent over the local network to the facility's Ovamha server, written to a temporary file, transcribed on that machine by the offline speech model, and **the file is deleted**, also if transcription fails | `apps/prototype/src/ovamha_proto/server.py` `_transcribe_upload`; `asr.py` |
| 4. Confirm | The worker sees the text, corrects or confirms each item. Only confirmed items are kept; unconfirmed text is discarded when the encounter closes | `confirm.py`, architecture DEV-03 |
| 5. Read aloud | When the app reads her details aloud (her description, card number, handover), the generated audio is a one-off file deleted once it has played; leftovers are removed when the server starts | `server.py` `do_speak`, `_start_sync`; `tts.py` `speak(cache=False)` |

The transcript is not logged. The audit trail records that an action happened, never what was said
(`audit.py` refuses names, transcripts, phone numbers and similar keys).

## Never used for training

- **App recordings and transcripts**: no code path stores them, so they cannot be used for training.
  The test `tests/prototype/test_privacy.py::test_training_code_never_reads_app_data` checks that the
  training code does not read the registry, outbox or audit files.
- **Speech model** (Whisper): fine-tuned only on public datasets (AfriSpeech-200, Google FLEURS) in the
  Kaggle notebook. See `ml/notebooks/README.md`.
- **Text classifier**: trained only on template sentences we wrote (`ml/textclf/make_training_data.py`)
  and the curated text set in `ml/eval/text/` (synthetic sentences and public AfriSpeech transcripts).
- **Evaluation recordings** (`ml/eval/RECORDING_GUIDE.md`): health workers acting out made-up scenario
  cards, never real patients. Their consent covers **testing only**, so these recordings must not be
  used for training. The notebook's `RUN = "csv"` option may be used for training only with a separate
  consent that says so, and approval as below.

## Before recording any person

Recording people to test or train models is health research under the MoHS Health Information System
Policy 2021, s.3.5.10(d): it needs written ethical clearance from the **Sierra Leone Ethics and
Scientific Review Committee (SLESRC)**. Voices are personal data; under the draft Data Protection
Bill 2025 consent must be freely given, informed and specific (s.37). Use the consent text in
`ml/eval/RECORDING_GUIDE.md`, and keep signed copies.

## Sources

- MoHS Sierra Leone, *Health Information System Policy* (2021), s.3.5.10(d).
- *Data Protection and Right to Access Information Regulatory Commission Bill* (2025, not yet law), s.26(1)(c)-(d), s.27(1), s.37, s.39(1).
- Ovamha architecture, DEV-03 ("Unconfirmed drafts and audio MUST be held outside the FHIR Engine and deleted when the encounter closes").
