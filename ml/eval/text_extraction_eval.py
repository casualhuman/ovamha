"""Score the prototype's danger-sign detection on the mixed maternal-health text set.

Text only: this measures extraction + safety net on correct transcripts, not speech
recognition. Two views per sign:
  extraction  - the field is captured as a current positive (what reaches the rules once confirmed)
  + safety net - extraction OR a safety-net flag (what the worker is asked about)
A label means the sign is present or recently experienced (see ml/eval/text/README.md), so
past-but-recent mentions are positives: the safety net, not extraction, is meant to catch those.

Usage: .venv/bin/python ml/eval/text_extraction_eval.py [--misses SIGN]
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/prototype/src"))

from ovamha_proto.extract import extract  # noqa: E402
from ovamha_proto.safety_net import LABELS, scan  # noqa: E402

DATA = ROOT / "ml/eval/text/maternal_health_afrispeech_mixed_500.csv"


def predict(text: str) -> tuple[set[str], set[str]]:
    ex = extract(text, "en")
    fields = {f for f, v in ex.fields.items() if f in LABELS and v.value is True}
    flags = {fl.field for fl in scan(ex)}
    return fields, fields | flags


def prf(tp: int, fp: int, fn: int) -> tuple[float, float]:
    p = tp / (tp + fp) if tp + fp else float("nan")
    r = tp / (tp + fn) if tp + fn else float("nan")
    return p, r


def score(rows, view: int):
    """Micro and per-sign counts; view 0 = extraction, 1 = extraction + safety net."""
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
    a = ap.parse_args()

    rows = []
    with open(DATA, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gold = {s for s in r["labels"].split(";") if s and s != "none"}
            rows.append({**r, "gold": gold, "pred": predict(r["text"])})

    print(f"{len(rows)} rows from {DATA.relative_to(ROOT)}\n")
    for title, subset in [("ALL", rows),
                          ("synthetic (E001-E400)", [r for r in rows if r["source"] == "synthetic_maternal"]),
                          ("AfriSpeech originals (E401-E500)", [r for r in rows if r["source"] != "synthetic_maternal"])]:
        print(f"== {title}: {len(subset)} rows")
        for view, name in [(0, "extraction"), (1, "+ safety net")]:
            _, (tp, fp, fn) = score(subset, view)
            p, rc = prf(tp, fp, fn)
            clean = sum(1 for r in subset if not r["gold"] and not r["pred"][view])
            neg = sum(1 for r in subset if not r["gold"])
            print(f"  {name:13} precision {fmt(p)}%  recall {fmt(rc)}%  (tp {tp}, fp {fp}, fn {fn}); "
                  f"'none' rows with no alarm: {clean}/{neg}")
        print()

    print("== per sign, all rows        extraction (P / R)    + safety net (P / R)")
    per0, _ = score(rows, 0)
    per1, _ = score(rows, 1)
    for s in sorted(set(per0) | set(per1)):
        p0, r0 = prf(*per0[s]); p1, r1 = prf(*per1[s])
        print(f"  {s:24} {fmt(p0)} / {fmt(r0)}        {fmt(p1)} / {fmt(r1)}")

    print("\n== recall by category (+ safety net), rows with at least one label")
    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
    for cat, subset in sorted(by_cat.items()):
        _, (tp, fp, fn) = score(subset, 1)
        neg = [r for r in subset if not r["gold"]]
        alarms = sum(1 for r in neg if r["pred"][1])
        rc = prf(tp, fp, fn)[1]
        print(f"  {cat:11} recall {fmt(rc)}%  false alarms on unlabelled rows: {alarms}/{len(neg)}")

    if a.misses:
        print(f"\n== misses / false alarms (+ safety net) for {a.misses}")
        for r in rows:
            gold, pred = r["gold"], r["pred"][1]
            missed, extra = gold - pred, pred - gold
            if a.misses != "all":
                missed, extra = missed & {a.misses}, extra & {a.misses}
            if missed or extra:
                print(f"  {r['id']} [{r['category']}] missed={sorted(missed)} extra={sorted(extra)}\n    {r['text'].strip()}")


if __name__ == "__main__":
    main()
