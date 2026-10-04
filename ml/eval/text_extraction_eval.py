"""Score the prototype's danger-sign detection on the mixed maternal-health text set.

Text only: this measures detection on correct transcripts, not speech recognition. Views:
  rules: extraction - lexicon field captured as a current positive
  rules + net       - lexicon extraction OR a safety-net flag (what the worker is asked about)
  classifier        - the fine-tuned text classifier (ml/textclf), if installed
  both              - classifier OR rules + net
The classifier trained on E001-E200, so its fair numbers are the HELD-OUT rows (E201-E500).
A label means the sign is present or recently experienced (see ml/eval/text/README.md), so
past-but-recent mentions are positives: the safety net, not extraction, is meant to catch those.

Usage: .venv/bin/python ml/eval/text_extraction_eval.py [--misses SIGN|all] [--view classifier]
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/prototype/src"))

from ovamha_proto import classifier as clf_mod  # noqa: E402
from ovamha_proto.extract import extract  # noqa: E402
from ovamha_proto.safety_net import LABELS, scan  # noqa: E402

DATA = ROOT / "ml/eval/text/maternal_health_afrispeech_mixed_500.csv"


CLF = clf_mod.load()
VIEWS = ["rules: extraction", "rules + net"] + (["classifier", "both"] if CLF else [])


def predict(text: str) -> list[set[str]]:
    ex = extract(text, "en")
    fields = {f for f, v in ex.fields.items() if f in LABELS and v.value is True}
    net = fields | {fl.field for fl in scan(ex)}
    if not CLF:
        return [fields, net]
    c = {h.sign for h in CLF.predict(text)}
    return [fields, net, c, c | net]


def prf(tp: int, fp: int, fn: int) -> tuple[float, float]:
    p = tp / (tp + fp) if tp + fp else float("nan")
    r = tp / (tp + fn) if tp + fn else float("nan")
    return p, r


def score(rows, view: int):
    """Micro and per-sign counts for one view (index into VIEWS)."""
    per = defaultdict(lambda: [0, 0, 0])  # tp, fp, fn
    for r in rows:
        gold, pred = r["gold"], r["pred"][view]
        for s in gold | pred:
            per[s][0 if s in gold and s in pred else 1 if s in pred else 2] += 1
    tot = [sum(v[i] for v in per.values()) for i in range(3)]
    return per, tot


def fmt(x: float) -> str:
    return "  -  " if x != x else f"{100 * x:5.1f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--misses", help="print missed and false-alarm rows for this sign (or 'all')")
    ap.add_argument("--view", default="classifier", help="view for --misses: " + ", ".join(VIEWS))
    a = ap.parse_args()

    rows = []
    with open(DATA, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gold = {s for s in r["labels"].split(";") if s and s != "none"}
            rows.append({**r, "gold": gold, "pred": predict(r["text"])})

    print(f"{len(rows)} rows from {DATA.relative_to(ROOT)}")
    if CLF:
        print(f"classifier: {clf_mod.MODEL_DIR.relative_to(ROOT)} (threshold {CLF.threshold})")
    else:
        print("classifier: not installed (train with ml/textclf/train.py)")
    print()
    held = {f"E{i:03d}" for i in range(201, 501)}
    subsets = [("HELD-OUT synthetic (E201-E400)", [r for r in rows if r["id"] in held and r["source"] == "synthetic_maternal"]),
               ("HELD-OUT AfriSpeech originals (E401-E500)", [r for r in rows if r["source"] != "synthetic_maternal"]),
               ("dev rows (E001-E200; classifier trained on these)", [r for r in rows if r["id"] not in held])]
    for title, subset in subsets:
        print(f"== {title}: {len(subset)} rows")
        for view, name in enumerate(VIEWS):
            _, (tp, fp, fn) = score(subset, view)
            p, rc = prf(tp, fp, fn)
            clean = sum(1 for r in subset if not r["gold"] and not r["pred"][view])
            neg = sum(1 for r in subset if not r["gold"])
            print(f"  {name:18} precision {fmt(p)}%  recall {fmt(rc)}%  (tp {tp:3}, fp {fp:3}, fn {fn:3}); "
                  f"no alarm on 'none' rows: {clean}/{neg}")
        print()

    test = [r for r in rows if r["id"] in held]
    print("== per sign, held-out rows (P / R)  " + "  ".join(f"{n:>17}" for n in VIEWS))
    pers = [score(test, v)[0] for v in range(len(VIEWS))]
    for s_ in sorted(set().union(*pers)):
        cells = []
        for per in pers:
            p, rc = prf(*per[s_])
            cells.append(f"{fmt(p)} / {fmt(rc)}")
        print(f"  {s_:24}" + "  ".join(f"{c:>17}" for c in cells))

    best = len(VIEWS) - 2 if CLF else 1
    print(f"\n== by category, held-out rows ({VIEWS[best]})")
    by_cat = defaultdict(list)
    for r in test:
        by_cat[r["category"]].append(r)
    for cat, subset in sorted(by_cat.items()):
        _, (tp, fp, fn) = score(subset, best)
        neg = [r for r in subset if not r["gold"]]
        alarms = sum(1 for r in neg if r["pred"][best])
        print(f"  {cat:11} recall {fmt(prf(tp, fp, fn)[1])}%  false alarms on unlabelled rows: {alarms}/{len(neg)}")

    if a.misses:
        v = VIEWS.index(a.view)
        print(f"\n== misses / false alarms ({a.view}) for {a.misses}")
        for r in rows:
            gold, pred = r["gold"], r["pred"][v]
            missed, extra = gold - pred, pred - gold
            if a.misses != "all":
                missed, extra = missed & {a.misses}, extra & {a.misses}
            if missed or extra:
                print(f"  {r['id']} [{r['category']}] missed={sorted(missed)} extra={sorted(extra)}\n    {r['text'].strip()}")


if __name__ == "__main__":
    main()
