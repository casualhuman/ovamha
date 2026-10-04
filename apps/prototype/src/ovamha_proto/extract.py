"""Transcript -> structured fields, using a per-language lexicon and regex.

Every field is either captured (True/False, with the evidence text) or explicitly
"not captured". Mentions that are negated count as False; mentions in the past or
described as resolved are NOT captured here. The safety net raises them instead.
All output is a *proposal*: nothing here reaches a rule until the worker confirms it.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .lexicon import (
    FIELD_TERMS,
    HEAVY_TERMS,
    LIGHT_TERMS,
    NEGATIONS,
    NUMBER_WORDS_EN,
    ONGOING,
    PAST_OR_RESOLVED,
    UNITS_EN,
    WEEKS_WORDS,
)

NOT_CAPTURED = "not captured"
FIELDS = list(FIELD_TERMS)  # symptom fields, in read-back order
# "blood pressure", "blood test" etc. are not bleeding.
BLOOD_PRESSURE_WORDS = {"pressure", "presha", "preshɔ", "prɛshɔ", "test", "tests", "group", "sugar", "donor", "transfusion", "count"}


def normalise(text: str) -> str:
    """Lowercase, strip tone marks/diacritics (keeps ɔ and ɛ), collapse whitespace."""
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def clauses(text: str) -> list[str]:
    return [c.strip() for c in re.split(r"[.;!?,\n]+", normalise(text)) if c.strip()]


def _terms(table: dict[str, list[str]], lang: str) -> list[str]:
    # Always include English: code-switching is common in all three languages.
    terms = list(table.get(lang, [])) + (list(table.get("en", [])) if lang != "en" else [])
    return [normalise(t) for t in terms]


def _term_pattern(term: str, lang: str) -> str:
    if lang == "yo":
        # Yoruba ASR often splits words at syllables ("e je" for eje, "da ku" for daku).
        return r"\s?".join(re.escape(c) for c in term.replace(" ", ""))
    return re.escape(term)


def _has_phrase(clause: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", clause) is not None


@dataclass
class Mention:
    field: str
    term: str
    clause: str
    negated: bool
    past: bool


def find_mentions(text: str, lang: str, table: dict[str, dict[str, list[str]]]) -> list[Mention]:
    negs = _terms(NEGATIONS, lang)
    pasts = _terms(PAST_OR_RESOLVED, lang)
    ongoing = _terms(ONGOING, lang)
    out: list[Mention] = []
    for clause in clauses(text):
        past = any(_has_phrase(clause, p) for p in pasts) and not any(_has_phrase(clause, o) for o in ongoing)
        for fname, by_lang in table.items():
            for term in sorted(set(_terms(by_lang, lang)), key=len, reverse=True):
                m = re.search(rf"(?<!\w){_term_pattern(term, lang)}(?!\w)", clause)
                if not m:
                    continue
                after = clause[m.end():].split()
                if after and after[0] in BLOOD_PRESSURE_WORDS:
                    continue  # "blood pressure" is not bleeding
                before = " ".join(clause[: m.start()].split()[-3:])
                negated = any(_has_phrase(before, n) for n in negs)
                near_past = past
                if past and lang == "yo":
                    # Yoruba ASR output has no punctuation, so one "clause" can hold several signs:
                    # a time word only applies to the sign just before or after it.
                    near = " ".join(clause[: m.start()].split()[-2:] + clause[m.end():].split()[:2])
                    near_past = any(_has_phrase(near, p) for p in pasts)
                out.append(Mention(fname, term, clause, negated, near_past))
                break  # one mention per field per clause
    return out


@dataclass
class FieldValue:
    value: object  # True / False / int / str / NOT_CAPTURED
    evidence: str = ""

    @property
    def captured(self) -> bool:
        return self.value != NOT_CAPTURED


@dataclass
class Extraction:
    lang: str
    transcript: str
    fields: dict[str, FieldValue] = field(default_factory=dict)
    mentions: list[Mention] = field(default_factory=list)


def _gestational_age(text: str, lang: str) -> FieldValue:
    t = normalise(text)
    weeks = "|".join(re.escape(w) for w in _terms(WEEKS_WORDS, lang))
    m = re.search(rf"(\d{{1,2}})\s*(?:{weeks})(?!\w)", t) or re.search(rf"(?:{weeks})\s*(\d{{1,2}})(?!\w)", t)
    if m:
        return FieldValue(int(m.group(1)), m.group(0))
    tens = "|".join(NUMBER_WORDS_EN)
    m = re.search(rf"\b({tens})(?:[ -]({'|'.join(UNITS_EN)}))?\s*(?:{weeks})\b", t)
    if m:
        n = NUMBER_WORDS_EN[m.group(1)] + (UNITS_EN[m.group(2)] if m.group(2) else 0)
        return FieldValue(n, m.group(0))
    return FieldValue(NOT_CAPTURED)


def _bleeding_amount(clause: str, lang: str) -> str:
    if any(_has_phrase(clause, h) for h in _terms(HEAVY_TERMS, lang)):
        return "heavy"
    if any(_has_phrase(clause, w) for w in _terms(LIGHT_TERMS, lang)):
        return "light"
    return NOT_CAPTURED


def extract(transcript: str, lang: str = "en") -> Extraction:
    ex = Extraction(lang=lang, transcript=transcript)
    ex.mentions = find_mentions(transcript, lang, FIELD_TERMS)
    ex.fields["gestational_age_weeks"] = _gestational_age(transcript, lang)
    for fname in FIELDS:
        current = [m for m in ex.mentions if m.field == fname and not m.past]
        positive = [m for m in current if not m.negated]
        if positive:
            ex.fields[fname] = FieldValue(True, positive[0].clause)
        elif current:
            ex.fields[fname] = FieldValue(False, current[0].clause)
        else:
            ex.fields[fname] = FieldValue(NOT_CAPTURED)
    bleed = ex.fields["vaginal_bleeding"]
    ex.fields["bleeding_amount"] = (
        FieldValue(_bleeding_amount(bleed.evidence, lang), bleed.evidence) if bleed.value is True else FieldValue(NOT_CAPTURED)
    )
    if ex.fields["bleeding_amount"].value == NOT_CAPTURED:
        ex.fields["bleeding_amount"].evidence = ""
    return ex
