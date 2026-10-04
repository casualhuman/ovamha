"""Fine-tune the danger-sign text classifier.

Data split (the evaluation set's later rows are never seen in training or threshold choice):
  train      generated.jsonl (make_training_data.py) + E001-E200 minus the validation rows
  validation 40 random rows from E001-E200: picks the decision threshold (recall-weighted F2)
  test       E201-E400 (synthetic) and E401-E500 (AfriSpeech originals): ml/eval/text_extraction_eval.py

Output: ml/models/danger-sign-clf/ (weights, tokenizer, labels.json with labels and threshold).
Usage: .venv/bin/python ml/textclf/train.py [--base sentence-transformers/all-MiniLM-L6-v2] [--epochs 6]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import torch
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/prototype/src"))
from ovamha_proto.classifier import DangerSignClassifier, build_model  # noqa: E402

EVAL_CSV = ROOT / "ml/eval/text/maternal_health_afrispeech_mixed_500.csv"
GENERATED = Path(__file__).resolve().parent / "data/generated.jsonl"
OUT = ROOT / "ml/models/danger-sign-clf"
LABELS = ["vaginal_bleeding", "fainting", "dizziness", "headache", "visual_disturbance", "convulsions", "fever",
          "abdominal_pain", "breathing_difficulty", "unconscious", "vomiting", "reduced_fetal_movement",
          "waters_broken", "foul_discharge", "swelling"]
DEV_IDS = {f"E{i:03d}" for i in range(1, 201)}


def load_eval_rows(ids: set[str]) -> list[dict]:
    with open(EVAL_CSV, newline="", encoding="utf-8") as f:
        return [{"text": r["text"].strip(), "labels": [s for s in r["labels"].split(";") if s in LABELS], "id": r["id"]}
                for r in csv.DictReader(f) if r["id"] in ids]


def f_beta(tp: int, fp: int, fn: int, beta: float = 2.0) -> float:
    b2 = beta * beta
    return (1 + b2) * tp / ((1 + b2) * tp + b2 * fn + fp) if tp else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()
    random.seed(a.seed); torch.manual_seed(a.seed)

    dev = load_eval_rows(DEV_IDS)
    random.shuffle(dev)
    val, dev_train = dev[:40], dev[40:]
    generated = [json.loads(l) for l in GENERATED.read_text().splitlines()]
    train = generated + dev_train * 3   # upweight the hand-written dev rows
    print(f"train {len(train)} ({len(generated)} generated + {len(dev_train)} dev rows x3), val {len(val)}")

    tok = AutoTokenizer.from_pretrained(a.base)
    model = build_model(a.base, len(LABELS))
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    steps = a.epochs * ((len(train) + a.batch - 1) // a.batch)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / (0.1 * steps)) * max(0.0, 1 - s / steps))
    loss_fn = torch.nn.BCEWithLogitsLoss()

    def target(labels):
        return [1.0 if l in labels else 0.0 for l in LABELS]

    model.train()
    for ep in range(a.epochs):
        random.shuffle(train)
        total = 0.0
        for i in range(0, len(train), a.batch):
            batch = train[i:i + a.batch]
            enc = tok([b["text"] for b in batch], padding=True, truncation=True, max_length=128, return_tensors="pt")
            loss = loss_fn(model(enc["input_ids"], enc["attention_mask"]), torch.tensor([target(b["labels"]) for b in batch]))
            loss.backward(); opt.step(); sched.step(); opt.zero_grad()
            total += loss.item() * len(batch)
        print(f"epoch {ep + 1}: loss {total / len(train):.4f}")

    OUT.mkdir(parents=True, exist_ok=True)
    model.encoder.save_pretrained(OUT); tok.save_pretrained(OUT)
    torch.save(model.head.state_dict(), OUT / "head.pt")
    meta = {"labels": LABELS, "threshold": 0.5, "base": a.base, "languages": ["en"],
            "trained_on": "ml/textclf/data/generated.jsonl + E001-E200 (minus 40 validation rows)"}
    (OUT / "labels.json").write_text(json.dumps(meta, indent=1))

    # Threshold: best recall-weighted F2 on validation, using the same windowed predict as the app.
    clf = DangerSignClassifier(OUT)
    best = (0.0, 0.5)
    for th in [x / 100 for x in range(10, 91, 5)]:
        tp = fp = fn = 0
        for r in val:
            pred, gold = {h.sign for h in clf.predict(r["text"], th)}, set(r["labels"])
            tp += len(pred & gold); fp += len(pred - gold); fn += len(gold - pred)
        best = max(best, (f_beta(tp, fp, fn), th))
    meta["threshold"] = best[1]
    (OUT / "labels.json").write_text(json.dumps(meta, indent=1))
    print(f"threshold {best[1]} (validation F2 {best[0]:.3f}); saved to {OUT}")


if __name__ == "__main__":
    main()
