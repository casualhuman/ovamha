"""DAK question sets: visibility, validation, derived GA/EDD."""
from datetime import date

from ovamha_proto import questionnaire as qn

TODAY = date(2026, 10, 4)


def test_every_question_cites_a_dak_element():
    for name in ("anc-registration", "anc-profile"):
        for q in qn.questions(name):
            assert q["dak"].startswith(("ANC.A4", "ANC.B4", "ANC.B6")), q["id"]
            assert q["say"]["en"], q["id"]


def test_first_pregnancy_skips_past_pregnancy_questions():
    clean, problems = qn.validate("anc-profile", {"gravida": 1}, TODAY)
    asked = {p.split(":")[0] for p in problems}
    assert "Babies born alive" not in asked and "Problems in past pregnancies" not in asked
    assert "Long-term health conditions" in asked


def test_dont_know_accepted_and_kept():
    clean, _ = qn.validate("anc-profile", {"gravida": "unknown", "ttcv_doses": "unknown"}, TODAY)
    assert clean["gravida"] == "unknown" and clean["ttcv_doses"] == "unknown"


def test_none_cannot_combine():
    _, problems = qn.validate("anc-profile", {"chronic_conditions": ["none", "hiv"]}, TODAY)
    assert any("cannot be combined" in p for p in problems)


def test_outcomes_consistency():
    _, problems = qn.validate("anc-profile", {"gravida": 2, "stillbirths": 1, "miscarriages": 1}, TODAY)
    assert any("more than her past pregnancies" in p for p in problems)


def test_lmp_gives_ga_and_edd():
    d = qn.derived({"ga_source": "lmp", "lmp": "2026-03-22"}, TODAY)
    assert d == {"ga_weeks": 28.0, "edd": "2026-12-27"}


def test_lmp_in_future_rejected():
    _, problems = qn.validate("anc-profile", {"ga_source": "lmp", "lmp": "2026-12-01"}, TODAY)
    assert any("Last menstrual period" in p for p in problems)
