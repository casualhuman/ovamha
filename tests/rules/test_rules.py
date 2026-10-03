"""Boundary tests for the demo rules (handover section 7)."""
from datetime import date

import pytest

from ovamha_proto.rules import (
    DT01_SIGNS,
    UNKNOWN,
    anc_dt01_danger_signs,
    edd,
    evaluate,
    gestational_age_weeks,
    pre_eclampsia,
    questions_to_ask,
)

ALL_NO = {k: False for k in DT01_SIGNS} | {"headache": False, "visual_disturbance": False}


# ---------- ANC.DT.01 ----------

def test_dt01_fires_on_vaginal_bleeding():
    r = anc_dt01_danger_signs({"vaginal_bleeding": True})
    assert r.fired
    assert "Vaginal bleeding" in r.reasons
    assert "Urgent referral to hospital" in r.actions


def test_dt01_not_fired_only_when_all_signs_answered_no():
    assert anc_dt01_danger_signs(ALL_NO).status == "not_fired"


def test_dt01_unknown_is_not_normal():
    c = ALL_NO | {"fever": UNKNOWN}
    r = anc_dt01_danger_signs(c)
    assert r.status == "needs_data"
    assert r.missing == ["fever"]


def test_dt01_empty_input_needs_data():
    assert anc_dt01_danger_signs({}).status == "needs_data"


def test_dt01_headache_alone_does_not_fire():
    r = anc_dt01_danger_signs(ALL_NO | {"headache": True})
    assert r.status == "not_fired"


def test_dt01_headache_with_visual_disturbance_fires():
    r = anc_dt01_danger_signs(ALL_NO | {"headache": True, "visual_disturbance": True})
    assert r.fired


def test_danger_sign_means_no_further_questions():
    results = evaluate({"vaginal_bleeding": True})
    assert questions_to_ask(results) == []


# ---------- Pre-eclampsia ----------

def pe(sys_, dia, rs=None, rd=None, protein="++", severe=False):
    c = {"systolic": sys_, "diastolic": dia, "urine_protein": protein, "severe_pe_symptoms": severe}
    if rs is not None:
        c["systolic_repeat"] = rs
    if rd is not None:
        c["diastolic_repeat"] = rd
    return pre_eclampsia(c)


@pytest.mark.parametrize("sys_,expected", [(139, "not_fired"), (140, "fired"), (159, "fired"), (160, "not_fired")])
def test_pe_systolic_boundaries(sys_, expected):
    assert pe(sys_, 80, sys_, 80).status == expected


@pytest.mark.parametrize("dia,expected", [(89, "not_fired"), (90, "fired"), (109, "fired"), (110, "not_fired")])
def test_pe_diastolic_boundaries(dia, expected):
    assert pe(120, dia, 120, dia).status == expected


@pytest.mark.parametrize("protein,expected", [("negative", "not_fired"), ("+", "not_fired"), ("++", "fired"), ("+++", "fired")])
def test_pe_proteinuria(protein, expected):
    assert pe(145, 95, 145, 95, protein=protein).status == expected


def test_pe_missing_repeat_reading_prompts_not_assumes():
    r = pe(145, 95)
    assert r.status == "needs_data"
    assert "systolic_repeat" in r.missing and "diastolic_repeat" in r.missing


def test_pe_repeat_out_of_range_does_not_fire():
    assert pe(145, 95, 130, 85).status == "not_fired"


def test_pe_unknown_protein_prompts():
    r = pe(145, 95, 145, 95, protein=UNKNOWN)
    assert r.status == "needs_data"
    assert r.missing == ["urine_protein"]


def test_pe_severe_symptoms_excluded_with_note():
    r = pe(145, 95, 145, 95, severe=True)
    assert r.status == "not_fired"
    assert r.notes


def test_pe_severe_range_gets_note():
    r = pe(165, 112)
    assert r.status == "not_fired"
    assert any("160/110" in n for n in r.notes)


def test_pe_missing_bp_prompts():
    r = pre_eclampsia({})
    assert r.status == "needs_data"
    assert r.missing == ["systolic", "diastolic"]


def test_low_bp_90_60_does_not_fire_pe():
    # Demo scenario: BP 90/60 with bleeding.
    assert pe(90, 60, 90, 60).status == "not_fired"


# ---------- Derived values ----------

def test_ga_and_edd():
    lmp = date(2026, 3, 22)
    assert gestational_age_weeks(lmp, date(2026, 10, 4)) == pytest.approx(28.0)
    assert edd(lmp) == date(2026, 12, 27)
