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
    w = registry.register("nurse-test")
    found, err = registry.find(registry.display(w.card_code).lower())
    assert err == "" and found.woman_id == w.woman_id


def test_find_typo_message():
    w = registry.register("nurse-test")
    bad = w.card_code[:5] + ("A" if w.card_code[5] != "A" else "B")
    found, err = registry.find(bad)
    assert found is None and "typo" in err


def test_unknown_valid_code():
    found, err = registry.find(registry.new_code())
    assert found is None and "First visit" in err


def test_record_visit():
    w = registry.register("nurse-test")
    registry.record_visit(w.card_code)
    assert registry.find(w.card_code)[0].visits == 1


def test_no_personal_data_stored():
    w = registry.register("nurse-test")
    rec = registry.find(w.card_code)[0]
    assert set(vars(rec)) == {"woman_id", "card_code", "created_at", "created_by", "visits", "last_visit", "episode_id", "national_id"}
    assert rec.national_id is None
