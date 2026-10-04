"""Yoruba: wrong-script guard and keyword matching on real Yoruba ASR output (no punctuation, split syllables)."""
from ovamha_proto.asr import latin_share
from ovamha_proto.extract import extract


def found(text):
    return {f: v.value for f, v in extract(text, "yo").fields.items() if v.value != "not captured"}


def test_non_latin_output_is_rejected():
    assert latin_share("ల´నాలుటిల్తార్ప్వ్వల్త్నికాతాక్ం.") < 0.8  # base Whisper rambling in Telugu script
    assert latin_share("ẹ jẹ̀ ń jáde púpọ̀ ó dá kú lánàá") == 1.0


def test_split_syllables_still_match():
    assert found("ẹ jẹ̀ ń jáde púpọ̀")["vaginal_bleeding"] is True


def test_past_word_only_applies_to_the_nearby_sign():
    f = found("ẹ jẹ̀ ń jáde púpọ̀ ó dá kú lánàá")  # bleeding now; fainted yesterday
    assert f["vaginal_bleeding"] is True and f["bleeding_amount"] == "heavy"
    assert "fainting" not in f or f["fainting"] is not True


def test_negation():
    assert found("kò sí ẹ̀jẹ̀, orí ń fọ́ ọ") == {"vaginal_bleeding": False, "headache": True}
