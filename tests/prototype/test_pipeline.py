"""Extraction, safety net and the confirmation gate."""
from ovamha_proto.confirm import Session
from ovamha_proto.extract import NOT_CAPTURED, extract
from ovamha_proto.rules import evaluate, questions_to_ask
from ovamha_proto.safety_net import scan

SCENARIO_EN = (
    "She is 28 weeks pregnant and she has heavy vaginal bleeding since this morning. "
    "She fainted yesterday but is fine now. No fever."
)


def test_every_field_filled_or_not_captured():
    ex = extract(SCENARIO_EN, "en")
    for f, fv in ex.fields.items():
        assert fv.value is True or fv.value is False or fv.value == NOT_CAPTURED or isinstance(fv.value, (int, str)), f


def test_scenario_extraction():
    ex = extract(SCENARIO_EN, "en")
    assert ex.fields["vaginal_bleeding"].value is True
    assert ex.fields["bleeding_amount"].value == "heavy"
    assert ex.fields["gestational_age_weeks"].value == 28
    assert ex.fields["fever"].value is False
    assert ex.fields["fainting"].value == NOT_CAPTURED  # past mention: not a current field
    assert ex.fields["headache"].value == NOT_CAPTURED


def test_safety_net_flags_fainted_in_passing():
    ex = extract("she fainted yesterday but is fine now", "en")
    flags = scan(ex)
    assert [f.field for f in flags] == ["fainting"]


def test_safety_net_ignores_negated_and_captured():
    ex = extract("She is bleeding. No headache.", "en")
    assert scan(ex) == []


def test_blood_pressure_is_not_bleeding():
    ex = extract("blood pressure is fine", "en")
    assert ex.fields["vaginal_bleeding"].value == NOT_CAPTURED


def test_since_yesterday_is_current():
    ex = extract("bleeding since yesterday", "en")
    assert ex.fields["vaginal_bleeding"].value is True


def test_yoruba_without_tone_marks():
    ex = extract("Ẹ̀jẹ̀ ń jáde púpọ̀, ó dákú lánàá", "yo")
    assert ex.fields["vaginal_bleeding"].value is True
    assert [f.field for f in scan(ex)] == ["fainting"]


def test_no_field_reaches_rules_without_confirm():
    s = Session()
    ex = extract(SCENARIO_EN, "en")
    s.propose_from_extraction(ex)
    s.propose_flags(scan(ex))
    s.propose_keypad("systolic", 90)
    assert s.finalise() == {}  # nothing confirmed -> nothing counts
    assert s.proposals == {}


def test_confirmed_flow_fires_dt01_and_stops_questions():
    s = Session()
    ex = extract(SCENARIO_EN, "en")
    s.propose_from_extraction(ex)
    s.propose_flags(scan(ex))
    s.confirm("vaginal_bleeding")
    s.confirm("fainting")
    s.propose_keypad("systolic", 90)
    s.confirm("systolic")
    confirmed = s.finalise()
    assert "fever" not in confirmed  # proposed but never confirmed -> discarded
    results = evaluate(confirmed)
    assert results[0].rule_id == "ANC.DT.01" and results[0].fired
    assert questions_to_ask(results) == []


def test_worker_correction_recorded():
    s = Session()
    s.propose_from_extraction(extract("heavy bleeding", "en"))
    s.confirm("bleeding_amount", "light")
    assert s.confirmed["bleeding_amount"] == "light"
    assert s.sources["bleeding_amount"].endswith("worker-corrected")
    assert s.events[0].proposed == "heavy"


def test_abdominal_pain_without_severity_is_unknown_not_normal():
    from ovamha_proto.rules import anc_dt01_danger_signs

    r = anc_dt01_danger_signs({"abdominal_pain": True})
    assert "severe_abdominal_pain" in r.missing


import pytest  # noqa: E402

PARAPHRASES = [
    ("Blood is coming from down there", {"vaginal_bleeding"}),
    ("Her clothes are soaked with blood", {"vaginal_bleeding"}),
    ("She says her wrapper is red and wet", {"vaginal_bleeding"}),
    ("She has seen her period even though she is pregnant", {"vaginal_bleeding"}),
    ("Her head is pounding and she sees stars", {"headache", "visual_disturbance"}),
    ("The baby is not kicking like before", {"reduced_fetal_movement"}),
    ("Water is running down her legs", {"waters_broken"}),
    ("Her feet are swollen and her face is puffy", {"swelling"}),
    ("Her blood pressure is normal and her vision is fine", set()),
    ("We did a blood test today. No bleeding.", set()),
    ("Routine visit. She feels well. No bleeding, no headache, no fever. The baby is moving.", set()),
]


@pytest.mark.parametrize("text,expected", PARAPHRASES)
def test_everyday_phrasings_and_no_false_alarms(text, expected):
    ex = extract(text, "en")
    got = {f for f, v in ex.fields.items() if v.value is True} | {f.field for f in scan(ex)}
    assert got == expected
