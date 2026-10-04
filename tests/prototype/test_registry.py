"""Woman ID + card code (decision 9)."""
import pytest

from ovamha_proto import registry


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OVAMHA_DATA", str(tmp_path))


def test_new_code_valid_and_no_lookalikes():
    for _ in range(200):
        c = registry.new_code()
        assert registry.is_valid(c) and not set(c) & set("01OIL")


def test_single_typo_caught():
    c = registry.new_code()
    for i in range(6):
        for ch in registry.ALPHABET:
            if ch != c[i]:
                assert not registry.is_valid(c[:i] + ch + c[i + 1:])


def test_adjacent_swap_caught():
    c = registry.new_code()
    for i in range(5):
        if c[i] != c[i + 1]:
            assert not registry.is_valid(c[:i] + c[i + 1] + c[i] + c[i + 2:])


def test_register_and_find_with_dash_and_lowercase():
    w = registry.register("nurse-test", age_years=25)
    found, err = registry.find(registry.display(w.card_code).lower())
    assert err == "" and found.woman_id == w.woman_id


def test_find_typo_message():
    w = registry.register("nurse-test", age_years=25)
    bad = w.card_code[:5] + ("A" if w.card_code[5] != "A" else "B")
    found, err = registry.find(bad)
    assert found is None and "typo" in err


def test_unknown_valid_code():
    found, err = registry.find(registry.new_code())
    assert found is None and "First visit" in err


def test_record_visit():
    w = registry.register("nurse-test", age_years=25)
    registry.record_visit(w.card_code)
    assert registry.find(w.card_code)[0].visits == 1


def test_no_personal_data_stored():
    w = registry.register("nurse-test", age_years=25)
    rec = registry.find(w.card_code)[0]
    assert set(vars(rec)) == {"woman_id", "card_code", "created_at", "created_by", "visits", "last_visit", "episode_id",
                              "national_id", "birth_date", "birth_date_estimated", "details", "profile", "profile_at"}
    assert rec.national_id is None


from datetime import date  # noqa: E402

TODAY = date(2026, 10, 4)


def test_estimated_age_becomes_birth_year():
    w = registry.register("n", age_years=24, today=TODAY)
    assert w.birth_date == "2002" and w.birth_date_estimated


def test_exact_birth_date():
    w = registry.register("n", birth_date="2001-05-17", today=TODAY)
    assert w.birth_date == "2001-05-17" and not w.birth_date_estimated


@pytest.mark.parametrize("kw", [{}, {"age_years": 5}, {"age_years": 75}, {"birth_date": "2024-01-01"}, {"birth_date": "17/05/2001"}])
def test_birth_date_required_and_plausible(kw):
    with pytest.raises(ValueError):
        registry.register("n", today=TODAY, **kw)


def test_nin_needs_consent_and_number_never_stored():
    with pytest.raises(ValueError):
        registry.register("n", national_id="nin", consent=False, age_years=25)
    w = registry.register("n", national_id="nin", consent=True, age_years=25)
    assert w.national_id["document"] == "National ID (NIN)" and w.national_id["verified"] is False
    assert w.card_code  # a card number is still issued: the NIN is never a search key (ID-04)


def test_profile_saved_and_old_records_load(tmp_path):
    w = registry.register("n", age_years=30, details={"first_name": "Mariama"})
    w2 = registry.save_profile(w.card_code, {"gravida": 3})
    assert w2.profile == {"gravida": 3} and w2.profile_at and w2.details["first_name"] == "Mariama"
    # a record written by an older version (extra keys) still loads
    data = registry._load()
    data[w.card_code]["previous_pregnancies"] = 2
    registry._save(data)
    assert registry.find(w.card_code)[0].woman_id == w.woman_id


def test_demo_woman_seeded_valid_and_idempotent():
    assert registry.seed_demo(TODAY) == ["MAMA2A"]
    assert registry.seed_demo(TODAY) == []  # already there
    w, err = registry.find("mam-a2a")
    assert err == "" and w.profile["gravida"] == 3 and w.visits == 1
    from ovamha_proto import questionnaire
    clean, problems = questionnaire.validate("anc-profile", w.profile, TODAY)
    assert problems == [], problems  # the seeded history passes the same checks as a real one
    assert questionnaire.derived(w.profile, TODAY)["ga_weeks"] == 20.0
