import pytest

from ovamha_proto.numbers import parse_bp, parse_number


@pytest.mark.parametrize("text,expected", [
    ("140", 140),
    ("one hundred and forty", 140),
    ("One hundred forty.", 140),
    ("ninety", 90),
    ("twenty eight weeks", 28),
    ("28 weeks", 28),
    ("thirty seven point five", 37.5),
    ("37.5", 37.5),
    ("one hundred and five", 105),
    ("fifteen", 15),
    ("fifty", 50),
])
def test_parse_number(text, expected):
    assert parse_number(text) == expected


@pytest.mark.parametrize("text", ["", "I don't know", "140 or 150"])
def test_ambiguous_or_missing_returns_none(text):
    assert parse_number(text) is None


@pytest.mark.parametrize("text,expected", [
    ("140 over 90", (140, 90)),
    ("140/90", (140, 90)),
    ("one hundred and forty over ninety", (140, 90)),
    ("one forty over ninety", (140, 90)),
    ("ninety over sixty", (90, 60)),
])
def test_parse_bp(text, expected):
    assert parse_bp(text) == expected


def test_bp_without_over_is_none():
    assert parse_bp("140 90") is None
