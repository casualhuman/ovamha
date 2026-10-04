"""DAK-based question sets (content/questions/*.json): ANC.A4 registration details and the
ANC.B6 first-contact profile. Screens, validation, read-aloud, handover lines and FHIR
Observations are all generated from these files, so each answer stays traceable to its
WHO DAK data element ID.

Answers: single -> option value; multi -> list of values; count -> int or "unknown";
date -> "YYYY-MM-DD"; text/phone -> str. "unknown" (Don't know) is recorded as such and
never treated as normal.
"""
from __future__ import annotations

import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from .rules import edd, gestational_age_weeks

QUESTIONS = Path(__file__).resolve().parents[4] / "content" / "questions"


@lru_cache(maxsize=4)
def load(name: str) -> dict:
    return json.loads((QUESTIONS / f"{name}.json").read_text())


def questions(name: str) -> list[dict]:
    return [q for s in load(name)["sections"] for q in s["questions"]]


def find_question(name: str, qid: str) -> dict | None:
    return next((q for q in questions(name) if q["id"] == qid), None)


def _cond(value, rule) -> bool:
    if rule == "any":
        return value not in (None, "", [])
    if isinstance(rule, str) and rule.startswith("gt"):
        return isinstance(value, int) and value > int(rule[2:])
    if isinstance(rule, list):
        return value in rule
    return value == rule


def visible(q: dict, answers: dict) -> bool:
    return all(_cond(answers.get(k), rule) for k, rule in q.get("show_if", {}).items())


def say(q: dict, lang: str, option: str | None = None) -> tuple[str, str]:
    """Read-aloud text for a question (or one of its options) and the language it is in."""
    if option is not None:
        opt = next((o for o in q.get("options", []) if o["value"] == option), None)
        if not opt:
            return option, "en"
        text = opt.get("say", {}).get(lang) if isinstance(opt.get("say"), dict) else None
        return (text, lang) if text else (opt["label"], "en")
    text = q.get("say", {}).get(lang)
    return (text, lang) if text else (q.get("say", {}).get("en") or q["label"], "en")


PHONE = re.compile(r"^\+?[0-9 ]{7,16}$")


def validate(name: str, answers: dict, today: date | None = None) -> tuple[dict, list[str]]:
    """Return (clean answers for visible questions only, list of problems)."""
    today = today or date.today()
    clean, problems = {}, []
    for q in questions(name):
        if not visible(q, {**answers, **clean}):
            continue
        v = answers.get(q["id"])
        if v in (None, "", []):
            if not q.get("optional"):
                hint = "please enter it" if q["type"] in ("text", "phone", "date") else "please answer (Don't know is allowed)"
                problems.append(f"{q['label']}: {hint}.")
            continue
        t = q["type"]
        values = {o["value"] for o in q.get("options", [])}
        if t == "single":
            if v not in values:
                problems.append(f"{q['label']}: choose one of the options.")
                continue
        elif t == "multi":
            if not isinstance(v, list) or not set(v) <= values:
                problems.append(f"{q['label']}: choose from the options.")
                continue
            exclusive = {o["value"] for o in q["options"] if o.get("exclusive")}
            if len(v) > 1 and set(v) & exclusive:
                problems.append(f"{q['label']}: 'None' or 'Don't know' cannot be combined with other answers.")
                continue
        elif t == "count":
            if v == "unknown" and q.get("dont_know"):
                pass
            else:
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    problems.append(f"{q['label']}: enter a number.")
                    continue
                if not q.get("min", 0) <= v <= q.get("max", 99):
                    problems.append(f"{q['label']}: {v} looks wrong.")
                    continue
        elif t == "date":
            try:
                d = date.fromisoformat(v)
            except (TypeError, ValueError):
                problems.append(f"{q['label']}: not a valid date.")
                continue
            if q["id"] == "lmp" and not 0 <= (today - d).days <= 44 * 7:
                problems.append("Last menstrual period: the date gives more than 44 weeks or a future date. Please check.")
                continue
        elif t == "phone":
            v = str(v).strip()
            if not PHONE.match(v):
                problems.append(f"{q['label']}: enter digits only, for example +232 76 123456.")
                continue
        elif t == "text":
            v = str(v).strip()[:80]
        clean[q["id"]] = v
    # Consistency of pregnancy outcomes (twins count as one pregnancy).
    g = clean.get("gravida")
    if isinstance(g, int):
        ended = [clean.get(k) for k in ("stillbirths", "miscarriages")]
        if all(isinstance(x, int) for x in ended) and sum(ended) > g - 1:
            problems.append("Stillbirths and miscarriages are more than her past pregnancies. Please check.")
    return clean, problems


def derived(profile: dict, today: date | None = None) -> dict:
    """GA and EDD from LMP (DAK: GA = (today - LMP)/7, EDD = LMP + 280 days)."""
    today = today or date.today()
    out = {}
    if profile.get("ga_source") == "lmp" and profile.get("lmp"):
        lmp = date.fromisoformat(profile["lmp"])
        out["ga_weeks"] = round(gestational_age_weeks(lmp, today), 1)
        out["edd"] = edd(lmp).isoformat()
    elif isinstance(profile.get("ga_weeks"), int):
        out["ga_weeks"] = profile["ga_weeks"]
    return out


def display(name: str, qid: str, v) -> str:
    q = find_question(name, qid)
    labels = {o["value"]: o["label"] for o in (q or {}).get("options", [])}
    if v == "unknown":
        return "not known"
    if isinstance(v, list):
        return ", ".join(labels.get(x, x) for x in v)
    return labels.get(v, str(v))


def handover_lines(name: str, answers: dict, skip: set[str] = frozenset()) -> list[str]:
    lines = []
    for q in questions(name):
        if q["id"] in answers and q["id"] not in skip:
            lines.append(f"  - {q['label']}: {display(name, q['id'], answers[q['id']])}")
    return lines
