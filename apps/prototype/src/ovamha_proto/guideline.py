"""National guideline advice (Sierra Leone Integrated Obstetric and Newborn Care Guideline, 2026 draft).

Advises the health worker; it never refers anyone. The worker reads the advice, with its
citation, and decides (see server: /api/decision). Content and citations live in
content/guidelines/sierra-leone-iong-2026.json; this module only evaluates them on
CONFIRMED data, alongside the WHO DAK demo rules in rules.py.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from .rules import RuleResult

GUIDE = Path(__file__).resolve().parents[4] / "content" / "guidelines" / "sierra-leone-iong-2026.json"
PRIORITY = {"urgent_referral": 0, "refer_cemonc": 1, "refer_assessment": 2, "plan_cemonc_delivery": 3, "check_now": 4}
KIND_TITLE = {
    "urgent_referral": "Consider urgent referral",
    "refer_cemonc": "Refer to a CEmONC facility",
    "refer_assessment": "Refer to CEmONC for assessment",
    "plan_cemonc_delivery": "High-risk: plan delivery at a CEmONC facility",
    "check_now": "Check now",
}


@lru_cache(maxsize=1)
def guide() -> dict:
    return json.loads(GUIDE.read_text())


@dataclass
class Advice:
    id: str
    kind: str
    title: str
    reasons: list[str]
    recommendation: str
    cite: str
    source: str = "Sierra Leone Integrated Obstetric and Newborn Care Guideline (2026 draft)"
    assumptions: list[str] = field(default_factory=list)

    @property
    def suggests_referral(self) -> bool:
        return self.kind in ("urgent_referral", "refer_cemonc", "refer_assessment", "plan_cemonc_delivery")


def _present(v, want) -> bool:
    return v == want or (want is True and v in ("severe", "mild"))


def _age(birth_date: str | None, today: date) -> int | None:
    if not birth_date:
        return None
    y = int(birth_date[:4])
    if len(birth_date) == 4:
        return today.year - y  # estimated birth year
    b = date.fromisoformat(birth_date)
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def _pe_class(c: dict, results: list[RuleResult]) -> tuple[str | None, str | None]:
    """Pre-eclampsia classification from the guideline's 'Classification after 20 weeks of pregnancy'."""
    sys_, dia, protein = c.get("systolic"), c.get("diastolic"), c.get("urine_protein")
    pe = any(r.rule_id == "ANC.PE" and r.fired for r in results)
    severe_range = isinstance(sys_, (int, float)) and isinstance(dia, (int, float)) and (sys_ >= 160 or dia >= 110)
    severe_signs = [lab for f, lab in (("headache", "severe headache"), ("visual_disturbance", "visual changes"),
                                       ("breathing_difficulty", "difficulty breathing")) if c.get(f) in (True, "severe")]
    if c.get("severe_pe_symptoms") is True:
        severe_signs.append("symptoms of severe pre-eclampsia")
    if (pe or severe_range) and (c.get("convulsions") is True or c.get("unconscious") is True):
        return "eclampsia", "Pre-eclampsia with convulsions or unconsciousness"
    if severe_range and protein in ("++", "+++"):
        return "severe", f"BP {sys_}/{dia} (160/110 or above) with proteinuria {protein}"
    if pe and severe_signs:
        return "severe", "Pre-eclampsia with " + ", ".join(severe_signs)
    if severe_range and protein in (None, "unknown"):
        return "check_protein", f"BP {sys_}/{dia} is 160/110 or above"
    if pe:
        return "mild", "Pre-eclampsia (BP 140/90 or above on two readings with proteinuria 2+)"
    return None, None


def advise(confirmed: dict, results: list[RuleResult], profile: dict | None = None, birth_date: str | None = None,
           facility_level: str = "CHP", today: date | None = None) -> list[Advice]:
    today = today or date.today()
    g = guide()
    c, p = confirmed, profile or {}
    out: list[Advice] = []

    # 1. Danger signs in pregnancy (Table 3.3).
    ds = g["danger_signs_pregnancy"]
    present = [s["label"] for s in ds["signs"] if any(_present(c.get(f), want) for f, want in s["fields"].items())]
    if present:
        out.append(Advice("SL.T3.3", "urgent_referral", "Danger sign in pregnancy", present, ds["advice"], ds["_cite"]))

    # 2. Pre-eclampsia classification (hypertension in pregnancy section).
    cls, why = _pe_class(c, results)
    cite_pe = "Pre-eclampsia and eclampsia: classification after 20 weeks of pregnancy; Table: high-risk conditions and recommendations"
    if cls in ("severe", "eclampsia"):
        out.append(Advice("SL.SPE", "urgent_referral", "Severe pre-eclampsia" if cls == "severe" else "Eclampsia", [why],
                          "Life-threatening emergency. Stabilise and start magnesium sulphate per your level of care, "
                          "then refer to a CEmONC facility for delivery and further management. Do not wait 4 hours to repeat BP.", cite_pe))
    elif cls == "check_protein":
        out.append(Advice("SL.SPE.check", "check_now", "Possible severe pre-eclampsia", [why],
                          "Check urine protein now. If severe pre-eclampsia is suspected, do NOT wait 4 hours to repeat the BP.", cite_pe))

    # 3. High-risk pregnancy (Table 3.4), from confirmed data, her profile and her age.
    age = _age(birth_date, today)
    fhr = c.get("fetal_heart_rate")
    lower = facility_level in g["facility_levels"]["lower"]
    for grp in g["high_risk"]["groups"]:
        hits, notes = [], []
        for cond in grp["conditions"]:
            m = cond["match"]
            hit = False
            for k, want in m.items():
                if k == "rule":
                    hit |= (want == "ANC.PE" and cls == "mild") or (want == "ANC.PE.severe" and cls in ("severe", "eclampsia"))
                elif k == "age_below":
                    hit |= age is not None and age < want
                elif k == "age_at_least":
                    hit |= age is not None and age >= want
                elif k == "fetal_heart_rate_outside":
                    hit |= isinstance(fhr, (int, float)) and not want[0] <= fhr <= want[1]
                elif k.endswith("_at_least"):
                    v = p.get(k[: -len("_at_least")])
                    hit |= isinstance(v, int) and v >= want
                else:
                    v = p.get(k)
                    hit |= isinstance(v, list) and bool(set(v) & set(want))
            if hit:
                hits.append(cond["label"])
                if cond.get("assumption"):
                    notes.append(cond["assumption"])
        if hits and (lower or grp["kind"] == "urgent_referral"):
            if grp["id"] == "current_urgent" and any(a.id == "SL.SPE" for a in out):
                hits = [h for h in hits if "pre-eclampsia" not in h.lower()]
                if not hits:
                    continue
            out.append(Advice(f"SL.T3.4.{grp['id']}", grp["kind"], f"{grp['category']}", hits, grp["recommendation"],
                              g["high_risk"]["_cite"], assumptions=notes))

    return sorted(out, key=lambda a: PRIORITY[a.kind])


def top_suggestion(advice: list[Advice], dak_results: list[RuleResult]) -> str:
    """The strongest suggestion across national advice and WHO DAK rules: what the worker is asked to decide on."""
    kinds = [a.kind for a in advice if a.suggests_referral]
    if any(r.fired for r in dak_results):
        kinds.append("urgent_referral")
    return min(kinds, key=lambda k: PRIORITY[k]) if kinds else "none"


def next_contact(ga_weeks: float | None, today: date | None = None) -> dict:
    """Next ANC contact from the national 8-contact schedule (Table 3.2)."""
    today = today or date.today()
    sched = guide()["contact_schedule"]
    if ga_weeks is None:
        return {"text": "Set the next contact once gestational age is known (Table 3.2: 8 contacts).", "cite": sched["_cite"]}
    for ct in sched["contacts"]:
        if ct["week"] > ga_weeks:
            when = today + timedelta(days=round((ct["week"] - ga_weeks) * 7))
            return {"contact": ct["n"], "week": ct["week"], "date": when.isoformat(),
                    "text": f"Contact {ct['n']} at {ct['week']} weeks, around {when.strftime('%d %b %Y')}", "cite": sched["_cite"]}
    return {"text": sched["after_last"], "cite": sched["_cite"]}


def management(advice: list[Advice], confirmed: dict, ga_weeks: float | None) -> list[dict]:
    """Guideline management steps for the advice shown ("What you can do now"), transcribed and cited."""
    m = guide().get("management", {})
    ids = {a.id: a for a in advice}
    out = []
    for blk in m.get("blocks", []):
        hits = [ids[i] for i in blk["for"] if i in ids]
        if not hits:
            continue
        when = blk.get("when", {})
        if when.get("vaginal_bleeding") and confirmed.get("vaginal_bleeding") is not True:
            continue
        if "ga_at_least_or_unknown" in when and ga_weeks is not None and ga_weeks < when["ga_at_least_or_unknown"]:
            continue
        keys = [k.lower() for k in blk.get("when_reason_contains", [])]
        if keys and not any(k in r.lower() for a in hits for r in a.reasons for k in keys):
            continue
        out.append({"id": blk["id"], "title": blk["title"], "steps": blk["steps"], "for": [a.id for a in hits],
                    "cite": f"{Advice.source}: {blk['cite']}", "scope_note": m.get("scope_note", "")})
    return out


def routine_care(ga_weeks: float | None, first_contact: bool) -> dict | None:
    """Preventive care due at this contact (Table 3.2), plus first-contact tests."""
    r = guide().get("routine_by_contact")
    if not r:
        return None
    contacts = guide()["contact_schedule"]["contacts"]
    n = None
    if ga_weeks is not None:
        n = next((c["n"] for c in contacts if c["week"] >= ga_weeks - 2), contacts[-1]["n"])
    elif first_contact:
        n = 1
    if n is None:
        return None
    week = next(c["week"] for c in contacts if c["n"] == n)
    return {"contact": n, "week": week, "items": r["contacts"][str(n)],
            "tests": r["first_contact_tests"] if first_contact else [], "cite": f"{Advice.source}: {r['_cite']}"}


# ---------------------------------------------------------------- translation of the advice screen
# A phrasebook keyed by the exact English sentence: content/guidelines/<guide>.<lang>.json, plus the
# read-back field labels. Anything not in it stays in English, so a missing line never hides advice.
@lru_cache(maxsize=4)
def _phrasebook(lang: str) -> dict[str, str]:
    path = GUIDE.with_name(f"{GUIDE.stem}.{lang}.json")
    book = json.loads(path.read_text())["text"] if path.exists() else {}
    from .tts import phrases  # read-back labels: "Vaginal bleeding" -> "Ẹ̀jẹ̀ ń jáde lójú ara"
    p = phrases()
    labels = {p["en"]["fields"][k]: v for k, v in p.get(lang, {}).get("fields", {}).items() if v and k in p["en"]["fields"]}
    return {**labels, **book}


def tr(text: str, lang: str) -> str:
    return _phrasebook(lang).get(text, text) if lang != "en" else text


def localise(view: dict, lang: str) -> dict | None:
    """The advice screen's text in `lang`, alongside the English (which stays the record of what was shown)."""
    if lang == "en" or not _phrasebook(lang):
        return None
    t = lambda s: tr(s, lang)  # noqa: E731
    return {
        "advice": [{"kind_title": t(a["kind_title"]), "reasons": [t(r) for r in a["reasons"]], "recommendation": t(a["recommendation"])}
                   for a in view["advice"]],
        "rules": [{"reasons": [t(r) for r in r_["reasons"]], "actions": [t(x) for x in r_["actions"]]} for r_ in view["rules"]],
        "management": [{"title": t(m["title"]), "steps": [t(s) for s in m["steps"]], "scope_note": t(m["scope_note"])}
                       for m in view["management"]],
    }
