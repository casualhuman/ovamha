"""Danger-sign text classifier: transcript -> signs with a score and the sentence that triggered it.

A small fine-tuned encoder (see ml/textclf/train.py) reads the transcript sentence by
sentence (and adjacent pairs, so "Her sister has fits. She is fine." keeps its context)
and scores every sign. Like the lexicon, its output is only a proposal for the worker.

English only for now: it was trained on English sentences. Callers fall back to the
lexicon rules for other languages or when the model is not installed.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

MODEL_DIR = Path(os.environ.get(
    "OVAMHA_CLASSIFIER_DIR", Path(__file__).resolve().parents[4] / "ml/models/danger-sign-clf"))
LANGS = {"en"}


@dataclass
class Hit:
    sign: str
    score: float
    evidence: str


def sentences(text: str) -> list[str]:
    parts = [s.strip() for s in re.split(r"(?<=[.!?;])\s+|\n+", text) if s.strip()]
    return parts or [text.strip()]


def windows(text: str) -> list[tuple[str, list[int]]]:
    """(text to score, indices of its sentences): every sentence, plus each adjacent pair."""
    s = sentences(text)
    return [(x, [i]) for i, x in enumerate(s)] + [(f"{s[i - 1]} {s[i]}", [i - 1, i]) for i in range(1, len(s))]


def build_model(encoder_name_or_dir, n_labels: int):
    """Encoder + mean pooling + linear head (mean pooling matches how MiniLM was pretrained)."""
    import torch
    from transformers import AutoModel

    class MeanPoolClassifier(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = AutoModel.from_pretrained(encoder_name_or_dir)
            self.head = torch.nn.Linear(self.encoder.config.hidden_size, n_labels)

        def forward(self, input_ids, attention_mask, **_):
            h = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
            m = attention_mask.unsqueeze(-1).to(h.dtype)
            return self.head((h * m).sum(1) / m.sum(1).clamp(min=1e-6))

    return MeanPoolClassifier()


class DangerSignClassifier:
    def __init__(self, model_dir: Path = MODEL_DIR):
        import torch
        from transformers import AutoTokenizer

        meta = json.loads((model_dir / "labels.json").read_text())
        self.labels: list[str] = meta["labels"]
        self.threshold: float = meta["threshold"]
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = build_model(model_dir, len(self.labels))
        self.model.head.load_state_dict(torch.load(model_dir / "head.pt", map_location="cpu"))
        self.model.eval()
        self.torch = torch

    def scores(self, texts: list[str]) -> list[list[float]]:
        with self.torch.no_grad():
            enc = self.tok(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
            return self.torch.sigmoid(self.model(enc["input_ids"], enc["attention_mask"])).tolist()

    def predict(self, text: str, threshold: float | None = None) -> list[Hit]:
        """Signs scoring at or above the threshold. Evidence is the sentence with the highest
        own score for that sign, so a pair window never points at its neighbour sentence."""
        th = self.threshold if threshold is None else threshold
        sents, wins = sentences(text), windows(text)
        rows = self.scores([w for w, _ in wins])
        single = rows[:len(sents)]  # windows() lists single sentences first, in order
        best: dict[str, Hit] = {}
        for (_, idx), row in zip(wins, rows):
            for j, (sign, p) in enumerate(zip(self.labels, row)):
                if p >= th and (sign not in best or p > best[sign].score):
                    ev = sents[max(idx, key=lambda i: single[i][j])]
                    best[sign] = Hit(sign, round(p, 3), ev)
        return sorted(best.values(), key=lambda h: -h.score)


@lru_cache(maxsize=1)
def load() -> DangerSignClassifier | None:
    """The installed classifier, or None if the model has not been trained/installed."""
    if not (MODEL_DIR / "labels.json").exists():
        return None
    return DangerSignClassifier(MODEL_DIR)
