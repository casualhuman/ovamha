# Speech recognition fine-tuning notebook (Kaggle)

The notebook (kept outside the repo; latest copy `wbgsmallai_fixed.ipynb`) fine-tunes Whisper small, compresses it to int8 with CTranslate2 and re-measures it on CPU with faster-whisper. It reports word error rate (WER) and danger-term recall (did a danger sign that was said appear in the transcript?).

Two runs, chosen with `RUN` in Cell 2:

| Run | Base model | Data |
| --- | --- | --- |
| `accented_en` | `openai/whisper-small` | AfriSpeech-200, Nigerian-accented (Yoruba, Igbo) clinical English (CC BY-NC-SA 4.0) |
| `yoruba` | `LyngualLabs/whisper-small-yoruba` (Apache-2.0) | Google FLEURS Yoruba (CC BY 4.0); ships the base model unchanged if fine-tuning does not beat it on validation |

## Results so far: smoke tests only (4 October 2026)

200 training clips, 30 steps; not the full run. Treat as a pipeline check, not as performance.

| Run | Model | WER | Danger-term recall |
| --- | --- | --- | --- |
| Accented English (test: 60 plain + 16 danger-sign clips) | Base | 39.3% | 13 of 16 |
| | Fine-tuned | 30.3% | 15 of 16 |
| | Fine-tuned, int8 (253 MB) | 30.9% | 14 of 16 |
| Yoruba (test: 30 clips) | Base (LyngualLabs) | 56.0% | — (no danger signs in FLEURS) |
| | Fine-tuned (100 clips, overfitted) | 61.8% | — |

The int8 model transcribed 2 to 3 times faster than real time on 4 CPU threads. Full runs (3,000 clips per accent, 1,000 steps) are pending.

Voice data from the app is never used here: training uses public datasets only ([docs/privacy/voice-data.md](../../docs/privacy/voice-data.md)).
