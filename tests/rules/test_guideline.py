"""Sierra Leone guideline advice: suggests, never refers."""
from datetime import date

from ovamha_proto.guideline import advise, next_contact, top_suggestion
from ovamha_proto.rules import evaluate

TODAY = date(2026, 10, 4)


def adv(c, profile=None, birth_date="1996", level="CHP"):
    return advise(c, evaluate(c), profile, birth_date, level, TODAY)


def test_danger_sign_suggests_urgent_referral_with_citation():
    a = adv({"vaginal_bleeding": True})
    assert a[0].kind == "urgent_referral" and a[0].reasons == ["Vaginal bleeding"]
    assert "Table 3.3" in a[0].cite


def test_mild_headache_is_not_a_national_danger_sign_but_severe_is():
    assert not [x for x in adv({"headache": "mild"}) if x.id == "SL.T3.3"]
    assert [x for x in adv({"headache": "severe"}) if x.id == "SL.T3.3"]


def test_severe_pre_eclampsia_by_bp_and_protein():
    a = adv({"systolic": 165, "diastolic": 100, "urine_protein": "++"})
    assert a[0].id == "SL.SPE" and a[0].kind == "urgent_referral"
    assert "Do not wait 4 hours" in a[0].recommendation


def test_severe_bp_without_protein_asks_to_check_now():
    a = adv({"systolic": 165, "diastolic": 100})
    assert any(x.id == "SL.SPE.check" for x in a)


def test_pe_plus_visual_changes_is_severe():
    c = {"systolic": 145, "diastolic": 95, "systolic_repeat": 145, "diastolic_repeat": 95, "urine_protein": "++",
         "severe_pe_symptoms": False, "visual_disturbance": True}
    assert any(x.id == "SL.SPE" for x in adv(c))


def test_previous_caesarean_plans_cemonc_delivery_at_lower_level_only():
    p = {"past_complications": ["caesarean"]}
    assert [x.kind for x in adv({}, p) if x.id.endswith("previous")] == ["plan_cemonc_delivery"]
    assert not [x for x in adv({}, p, level="CEmONC") if x.id.endswith("previous")]


def test_age_and_conditions_from_profile():
    a = adv({}, {"chronic_conditions": ["sickle_cell", "hiv"]}, birth_date="2010")
    ids = {x.id for x in a}
    assert {"SL.T3.4.current_assessment", "SL.T3.4.medical_advanced", "SL.T3.4.medical_assessment"} <= ids


def test_high_parity_assumption_is_stated():
    a = adv({}, {"live_births": 6})
    prev = next(x for x in a if x.id.endswith("previous"))
    assert prev.assumptions and "assumption" not in prev.recommendation.lower()


def test_top_suggestion_and_none():
    c = {"vaginal_bleeding": True}
    assert top_suggestion(adv(c), evaluate(c)) == "urgent_referral"
    c = {"vaginal_bleeding": False}
    assert top_suggestion(adv(c), evaluate(c)) == "none"


def test_next_contact_schedule():
    assert next_contact(22, TODAY)["week"] == 26
    assert next_contact(40.5, TODAY)["text"].startswith("Refer to CEmONC for induction")
    assert "gestational age" in next_contact(None, TODAY)["text"]
