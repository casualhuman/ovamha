"""Detector modes: classifier, rules, both (with a stand-in classifier, so no model file is needed)."""
import pytest

from ovamha_proto import classifier
from ovamha_proto.classifier import Hit, windows
from ovamha_proto.confirm import Session
from ovamha_proto.detect import detect
from ovamha_proto.extract import NOT_CAPTURED

TEXT = "She has heavy vaginal bleeding since this morning. Her forehead is pounding. No fever."


class FakeClassifier:
    def __init__(self, hits):
        self.hits = hits

    def predict(self, text):
        return self.hits


HEADACHE = FakeClassifier([Hit("headache", 0.91, "Her forehead is pounding."),
                           Hit("vaginal_bleeding", 0.97, "She has heavy vaginal bleeding since this morning.")])


def test_rules_mode_is_unchanged():
    det = detect(TEXT, "en", "rules")
    assert det.mode == "rules" and det.field_source == "voice-ai-extracted"
    assert det.extraction.fields["vaginal_bleeding"].value is True
    assert det.extraction.fields["headache"].value == NOT_CAPTURED  # "forehead is pounding" is not in the lexicon


def test_classifier_mode_uses_classifier_positives_and_keeps_lexicon_negatives():
    det = detect(TEXT, "en", "classifier", clf=HEADACHE)
    f = det.extraction.fields
    assert det.mode == "classifier" and det.flags == []
    assert f["headache"].value is True and f["headache"].evidence == "Her forehead is pounding."
    assert f["vaginal_bleeding"].value is True
    assert f["bleeding_amount"].value == "heavy"
    assert f["fever"].value is False  # explicit "No fever" from the lexicon


def test_classifier_mode_drops_lexicon_only_positive():
    det = detect("She is bleeding.", "en", "classifier", clf=FakeClassifier([]))
    assert det.extraction.fields["vaginal_bleeding"].value == NOT_CAPTURED
    assert det.extraction.fields["bleeding_amount"].value == NOT_CAPTURED


def test_both_mode_adds_classifier_signs_as_flags():
    det = detect(TEXT, "en", "both", clf=HEADACHE)
    assert det.extraction.fields["vaginal_bleeding"].value is True  # from rules
    assert [(fl.field, fl.source) for fl in det.flags] == [("headache", "ai-classifier")]


def test_fallback_to_rules_for_unsupported_language():
    det = detect("A de blid", "kri", "classifier", clf=HEADACHE)
    assert det.mode == "rules" and "does not support kri" in det.notes[0]


def test_fallback_to_rules_when_model_missing(monkeypatch):
    monkeypatch.setattr(classifier, "load", lambda: None)
    det = detect(TEXT, "en", "classifier")
    assert det.mode == "rules" and "not installed" in det.notes[0]


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        detect(TEXT, "en", "magic")


def test_classifier_proposals_carry_their_source():
    s = Session()
    det = detect(TEXT, "en", "classifier", clf=HEADACHE)
    s.propose_from_extraction(det.extraction, det.field_source)
    assert s.proposals["headache"].source == "voice-ai-classifier"
    assert "headache" not in s.confirmed  # still needs the worker


def test_windows_keep_previous_sentence_as_context():
    w = windows("Her sister has fits. She is fine.")
    assert ("Her sister has fits. She is fine.", [0, 1]) in w


@pytest.mark.skipif(classifier.load() is None, reason="classifier model not installed (ml/textclf/train.py)")
def test_real_model_on_paraphrase_and_negation():
    clf = classifier.load()
    assert "vomiting" in {h.sign for h in clf.predict("She has thrown up three times since breakfast.")}
    assert clf.predict("She denies bleeding, headache and fever.") == []
    hits = {h.sign: h for h in clf.predict("She keeps bringing her food back up. Her sister had a seizure.")}
    assert hits["vomiting"].evidence == "She keeps bringing her food back up."
    assert "convulsions" not in hits
