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


def test_extra_words_inside_a_phrase():
    # Real app transcript of "Orí ń fọ́ ọ gidigidi, ara rẹ̀ sì gbóná" (headache, fever).
    f = found("orin ń fọ́ gidi gidi ara rẹ̀ sín gbọ́nà")
    assert f["headache"] is True and f["fever"] is True


# ---- Yoruba guideline advice
import json  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

from ovamha_proto import guideline  # noqa: E402
from ovamha_proto.rules import evaluate  # noqa: E402
from ovamha_proto.tts import mixed_segments  # noqa: E402

YO = json.loads((Path(guideline.GUIDE).with_name("sierra-leone-iong-2026.yo.json")).read_text())["text"]


def test_every_translation_keeps_the_same_numbers_and_doses():
    nums = lambda s: sorted(re.findall(r"\d+(?:\.\d+)?", s))  # noqa: E731
    for en, yo in YO.items():
        assert nums(en) == nums(yo), en


def test_every_guideline_sentence_on_the_advice_screen_is_translated():
    g = guideline.guide()
    need = [g["danger_signs_pregnancy"]["advice"], g["management"]["scope_note"]]
    need += [s["label"] for s in g["danger_signs_pregnancy"]["signs"]]
    for grp in g["high_risk"]["groups"]:
        need += [grp["category"], grp["recommendation"], *[c["label"] for c in grp["conditions"]]]
    for b in g["management"]["blocks"]:
        need += [b["title"], *b["steps"]]
    from ovamha_proto.rules import DT01_SIGNS
    need += list(DT01_SIGNS.values())  # WHO DAK danger signs shown on the same screen
    assert [n for n in need if n not in YO and guideline.tr(n, "yo") == n] == []


def test_localise_translates_advice_and_management_and_keeps_english():
    c = {"systolic": 165, "diastolic": 112, "urine_protein": "++", "headache": "severe"}
    adv = guideline.advise(c, evaluate(c), {"past_complications": ["pre_eclampsia"]}, "2002")
    view = {"advice": [{"kind_title": guideline.KIND_TITLE[a.kind], "reasons": a.reasons, "recommendation": a.recommendation} for a in adv],
            "rules": [], "management": guideline.management(adv, c, 32)}
    t = guideline.localise(view, "yo")
    assert any(a["recommendation"].startswith("Pàjáwìrì") for a in t["advice"])  # severe pre-eclampsia
    assert any("Orí fífọ́" in r for a in t["advice"] for r in a["reasons"])
    assert t["management"][0]["steps"][1].startswith("Ìwọ̀n àkọ́kọ́")
    assert view["management"][0]["steps"][1].startswith("Loading dose")  # English untouched
    assert guideline.localise(view, "en") is None


def test_doses_are_spoken_by_the_english_voice():
    segs = mixed_segments("Aspirin 75 mg lójoojúmọ́. Bí ìfúnpá bá ju 140/90 mmHg lọ", "yo")
    assert ("seventy five milligrams", "en") in segs and ("one hundred and forty over ninety", "en") in segs
    assert all(lang == "yo" for part, lang in segs if "lójoojúmọ́" in part)
