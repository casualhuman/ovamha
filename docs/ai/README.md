# AI in MaternaSave

Small, offline AI that helps the health worker capture what she sees, never AI that makes the clinical decision. **AI proposes, the worker confirms, cited guideline rules advise, the worker decides.** Why rules and not a generative model: [docs/decisions/guideline-advice-not-fine-tuning.md](../decisions/guideline-advice-not-fine-tuning.md).

## 1. The models

| Task | Model | Size | Runs | Licence |
| --- | --- | --- | --- | --- |
| Speech recognition | Whisper small via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2, int8) | about 250 MB (int8) | Offline, CPU | MIT ([Systran/faster-whisper-small](https://huggingface.co/Systran/faster-whisper-small)) |
| Speech recognition, fine-tuning (research) | Whisper small fine-tuned on Nigerian-accented clinical English (AfriSpeech-200); Yoruba: [LyngualLabs/whisper-small-yoruba](https://huggingface.co/LyngualLabs/whisper-small-yoruba) | 253 MB (int8, measured) | Offline, CPU | Apache-2.0 base; training data CC BY-NC-SA 4.0 |
| Danger-sign detection | Fine-tuned [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) sentence encoder, 15 danger signs | about 90 MB | Offline, CPU | Apache-2.0 |
| Danger-sign detection (fallback) | Keyword rules + AI safety net (English, draft Krio and Yoruba) | — | Offline | Ours |
| Read-aloud | [MMS-TTS](https://huggingface.co/facebook/mms-tts-eng) English, Krio, Yoruba voices | small per language | Offline, CPU | **CC BY-NC 4.0 (non-commercial)** |

Measured speed (Kaggle notebook, 4 CPU threads): the int8 Whisper model transcribes 2 to 3 times faster than real time. Speech fine-tuning results so far are smoke tests (200 training clips): accented English word error rate fell from 40% to 30%; see [ml/notebooks/README.md](../../ml/notebooks/README.md).

## 2. Understanding what the worker says: danger-sign detection

Speech is transcribed offline (Whisper small). MaternaSave then has to work out which danger signs were described, often in everyday words ("her wrapper is red", "she sees stars"). Two detectors are built in; the **text classifier is the default**, and everything either one proposes must be confirmed by the worker.

| Detector | How it works | Danger signs caught (recall) | Correct when it raises a sign (precision) | "No danger sign" rows left alone |
| --- | --- | --- | --- | --- |
| **Text classifier (default)** | A small fine-tuned sentence encoder ([all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), Apache 2.0, about 90 MB, runs offline on CPU) scores each sentence for 15 danger signs | **94.4%** (169 of 179) | **90.9%** | 42 of 50 |
| Keyword rules + AI safety net | Phrase list per danger sign, with negation ("no fever") and past-event ("fainted yesterday") handling | 48.0% (86 of 179) | 84.3% | 40 of 50 |

Measured on 200 held-out written descriptions (E201–E400 of [ml/eval/text](../../ml/eval/text/)) never used for training or tuning; full per-sign and per-category results in [ml/eval/results/text-detection-classifier-vs-rules.txt](../../ml/eval/results/text-detection-classifier-vs-rules.txt). The decision threshold (0.15) was chosen on separate validation rows to favour catching danger signs over avoiding false alarms, because every proposal is checked by the worker. How it was built: [ml/textclf/README.md](../../ml/textclf/README.md).

**Limits, stated plainly:** the held-out rows come from the same AI-written dataset as the training rows, so real spoken descriptions will score lower; it raised false alarms on 25 of 106 distractor sentences (signs about someone else, blood tests) and 6 of 34 denials; it is English only (Krio and Yoruba fall back to the keyword rules). Labels were curated by the team, not adjudicated by clinicians. Set `OVAMHA_DETECTOR=rules` or `both` to switch detector.

## 3. Responsible AI: WHO principles

WHO, [*Ethics and governance of artificial intelligence for health*](https://iris.who.int/handle/10665/341996) (2021), six principles:

| WHO principle | In MaternaSave |
| --- | --- |
| 1. Protect autonomy | The worker confirms every AI suggestion and makes every decision; declining a suggested referral needs a reason but the advice is never hidden; privacy and consent: [docs/privacy/README.md](../privacy/README.md) |
| 2. Promote well-being, safety and the public interest | AI may add a concern, never remove one (add-only safety net); unknown is never treated as normal; recall favoured over precision |
| 3. Transparency, explainability, intelligibility | Every proposal shows the sentence that triggered it; every suggestion cites its guideline table; measured results and limits published here |
| 4. Responsibility and accountability | FHIR Provenance records which model and which rule produced each item and who confirmed it; audit trail |
| 5. Inclusiveness and equity | Voice and read-aloud for low literacy; Krio and Yoruba alongside English; offline on low-cost devices |
| 6. Responsive and sustainable | Small open models, no cloud or per-use fees; a country adds its guideline and language models without changing the app |

## 4. Voice data

Recordings are transcribed, then deleted, and **never used for training**: [docs/privacy/voice-data.md](../privacy/voice-data.md).

## 5. Build and evaluation

- Text classifier: [ml/textclf/README.md](../../ml/textclf/README.md)
- Speech fine-tuning notebook: [ml/notebooks/README.md](../../ml/notebooks/README.md)
- Evaluation sets and protocol: [ml/eval/](../../ml/eval/), text set [ml/eval/text/README.md](../../ml/eval/text/README.md), recording guide [ml/eval/RECORDING_GUIDE.md](../../ml/eval/RECORDING_GUIDE.md)
- Results: [ml/eval/results/README.md](../../ml/eval/results/README.md)
