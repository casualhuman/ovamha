"""AI safety net: scan the whole transcript for danger-sign terms that extraction
did not capture as a current, positive field (for example, mentioned in passing
or in the past), and return them as flags for the worker to confirm.

Add-only: a flag can raise a question; it can never clear a field, delay a rule
prompt or override a rule. Unconfirmed flags are discarded by confirm.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from .extract import Extraction, _terms, clauses, find_mentions
from .lexicon import NEGATIONS
from .lexicon import FIELD_TERMS, SAFETY_NET_ONLY

LABELS = {
    "vaginal_bleeding": "Vaginal bleeding",
    "dizziness": "Dizziness",
    "fainting": "Fainting",
    "headache": "Headache",
    "visual_disturbance": "Visual disturbance",
    "convulsions": "Convulsions",
    "fever": "Fever",
    "abdominal_pain": "Abdominal pain",
    "breathing_difficulty": "Difficulty breathing",
    "unconscious": "Unconscious / not responding",
    "vomiting": "Vomiting",
    "reduced_fetal_movement": "Reduced fetal movement",
    "waters_broken": "Waters broken",
    "swelling": "Swelling",
    "foul_discharge": "Foul-smelling vaginal discharge",
}


@dataclass
class Flag:
    field: str
    label: str
    evidence: str
    reason: str
    source: str = "ai-safety-net"  # or "ai-classifier" (detect.py, mode "both")


def scan(ex: Extraction) -> list[Flag]:
    table = {**FIELD_TERMS, **SAFETY_NET_ONLY}
    flags: dict[str, Flag] = {}
    for m in find_mentions(ex.transcript, ex.lang, table):
        if m.negated:
            continue  # "no fever": nothing to raise
        fv = ex.fields.get(m.field)
        if fv is not None and fv.value is True:
            continue  # already captured as a current positive field
        if m.field in flags:
            continue
        reason = "mentioned in the past or as resolved" if m.past else "mentioned but not captured as a field"
        flags[m.field] = Flag(m.field, LABELS.get(m.field, m.field), m.clause, reason)
    if ex.lang != "en":  # speech recognition often gets one letter wrong in Krio and Yoruba
        for field, clause, term in near_mentions(ex.transcript, ex.lang, table):
            fv = ex.fields.get(field)
            if field in flags or (fv is not None and fv.captured):
                continue
            flags[field] = Flag(field, LABELS.get(field, field), clause, f"heard something close to “{term}”; please check")
    return list(flags.values())


def _distance(a: str, b: str, cap: int = 2) -> int:
    """Levenshtein distance, stopping early once it exceeds cap."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def near_mentions(text: str, lang: str, table: dict) -> list[tuple[str, str, str]]:
    """(field, clause, term) for multi-word local-language danger phrases heard with one letter wrong,
    e.g. "ore n fo" for "ori n fo" (her head is aching). Single words must match exactly, so short words
    like "iba" (fever) cannot raise false alarms. Negated phrases are skipped. Flags only: the worker decides."""
    negs = _terms(NEGATIONS, lang)
    out = []
    for clause in clauses(text):
        words = clause.split()
        for field, by_lang in table.items():
            for term in by_lang.get(lang, []):
                tw = term.split()
                if len(tw) < 2 or len(term) < 6:
                    continue
                for i in range(len(words) - len(tw) + 1):
                    window = " ".join(words[i:i + len(tw)])
                    if window != term and _distance(window, term) <= 1:
                        if any(n in words[max(0, i - 3):i] for n in negs):
                            continue
                        out.append((field, clause, term))
                        break
    return out
