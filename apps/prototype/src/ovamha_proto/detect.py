"""Danger-sign detection: transcript -> proposals, with a choice of detector.

Modes (env OVAMHA_DETECTOR, default "classifier"):
  classifier  the fine-tuned text classifier proposes the symptoms. The lexicon still
              supplies numbers (gestational age), bleeding amount and explicit "no X"
              answers, which the classifier does not output.
  rules       lexicon extraction + AI safety net only (the original behaviour).
  both        rules, plus every classifier sign the rules missed, raised as a flag.

The classifier is English-only and optional: for other languages, or if the model is
not installed, every mode falls back to rules and says so. All output is a proposal;
nothing counts until the worker confirms it (confirm.py).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import classifier
from .extract import NOT_CAPTURED, Extraction, FieldValue, _bleeding_amount, extract, normalise
from .safety_net import Flag, LABELS, scan

MODES = ("classifier", "rules", "both")


@dataclass
class Detection:
    extraction: Extraction
    flags: list[Flag]
    mode: str                     # the mode actually used
    field_source: str             # Proposal.source for extraction fields
    notes: list[str] = field(default_factory=list)


def detect(transcript: str, lang: str, mode: str | None = None, clf=None) -> Detection:
    mode = mode or os.environ.get("OVAMHA_DETECTOR", "classifier")
    if mode not in MODES:
        raise ValueError(f"unknown detector mode {mode!r}; expected one of {MODES}")
    ex = extract(transcript, lang)
    if mode == "rules":
        return Detection(ex, scan(ex), "rules", "voice-ai-extracted")

    clf = clf or classifier.load()
    if clf is None or lang not in classifier.LANGS:
        why = "the text classifier is not installed" if clf is None else f"the text classifier does not support {lang} yet"
        return Detection(ex, scan(ex), "rules", "voice-ai-extracted", [f"Used keyword rules: {why}."])
    hits = clf.predict(transcript)

    if mode == "both":
        flags = scan(ex)
        have = {f for f, v in ex.fields.items() if v.value is True} | {fl.field for fl in flags}
        flags += [Flag(h.sign, LABELS.get(h.sign, h.sign), h.evidence, f"text classifier, score {h.score:.2f}", "ai-classifier")
                  for h in hits if h.sign not in have]
        return Detection(ex, flags, "both", "voice-ai-extracted")

    # classifier: its positives replace the lexicon's; lexicon keeps numbers and explicit negatives.
    found = {h.sign: h for h in hits}
    for sign in set(LABELS) | set(found):
        fv = ex.fields.get(sign)
        if sign in found:
            ex.fields[sign] = FieldValue(True, found[sign].evidence)
        elif fv is not None and fv.value is True:
            ex.fields[sign] = FieldValue(NOT_CAPTURED)   # lexicon-only positive: the classifier decides
    bleed = ex.fields.get("vaginal_bleeding")
    if bleed is not None and bleed.value is True:
        amount = _bleeding_amount(normalise(bleed.evidence), lang)
        ex.fields["bleeding_amount"] = FieldValue(amount, bleed.evidence if amount != NOT_CAPTURED else "")
    else:
        ex.fields["bleeding_amount"] = FieldValue(NOT_CAPTURED)
    return Detection(ex, [], "classifier", "voice-ai-classifier")
