# Danger-sign text classifier

Reads a (transcribed) English description of the woman and proposes danger signs, with the
sentence that triggered each one. It is the app's default detector; the keyword rules
(`lexicon.py` + safety net) remain available as an option.

| Detector (`OVAMHA_DETECTOR`) | What proposes symptoms |
|---|---|
| `classifier` (default) | the classifier; the lexicon still supplies gestational age, bleeding amount and explicit "no X" answers |
| `rules` | lexicon extraction + AI safety net (original behaviour) |
| `both` | rules, plus any classifier sign the rules missed, shown as an "AI noticed this" flag |

Non-English transcripts, or a missing model, fall back to `rules` with a note. Everything is a
proposal until the worker confirms it.

## Build

```bash
.venv/bin/python ml/textclf/make_training_data.py   # 4,000 template sentences -> data/generated.jsonl
.venv/bin/python ml/textclf/train.py                # ~4 min on a laptop CPU -> ml/models/danger-sign-clf (87 MB, not committed)
.venv/bin/python ml/eval/text_extraction_eval.py    # classifier vs rules on ml/eval/text
```

Model: `sentence-transformers/all-MiniLM-L6-v2` encoder, mean pooling, 15 sigmoid outputs.
Training data: our template sentences + E001-E200 of the evaluation set (40 held for choosing
the threshold, F2 so recall counts more). E201-E500 are never used for training or tuning.

## Results (held-out, text only)

See `ml/eval/results/text-detection-classifier-vs-rules.txt`. On E201-E400: recall 94% vs 48%
for rules + safety net, precision 91% vs 84%.

## Limits

- Held-out rows come from the same synthetic set as the training rows, so they flatter the
  model. Real community-health conversations, spoken and then transcribed, will be harder.
- The AfriSpeech textbook sentences (E401-E500) still trigger false alarms (35 of 99).
- English only. Krio and Yoruba need labelled sentences in those languages.
- Labels are assistant-curated, not clinician-adjudicated.
