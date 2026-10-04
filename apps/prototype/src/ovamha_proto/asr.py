"""Offline ASR with faster-whisper (CTranslate2, int8).

English: the fine-tuned model from the notebook when available (set OVAMHA_ASR_EN
to its CTranslate2 directory), else Whisper small ("small" = Systran/faster-whisper-small,
a CTranslate2 conversion of openai/whisper-small). Models are downloaded once, then
run with no internet.

Yoruba: Whisper small's built-in Yoruba (weak) until LyngualLabs/whisper-small-yoruba is
converted (P2; set OVAMHA_ASR_YO). Krio: Whisper has no Krio; English decoding is used as a
labelled fallback until MMS (kri adapter) or DONDO is added (P2; set OVAMHA_ASR_KRI).

No speech enhancement (it degraded medical ASR in Chondhekar et al.). A quality gate
(length, clipping, level, speech present) asks the worker to repeat on failure.
"""
from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16_000
# Yoruba: LyngualLabs/whisper-small-yoruba (Apache 2.0) converted to CTranslate2 int8 by
# scripts/convert_yoruba_asr.sh; used automatically when present (not committed: weights).
_YO_LOCAL = Path(__file__).resolve().parents[4] / "ml/models/whisper-small-yoruba-ct2"
_YO_DEFAULT = str(_YO_LOCAL) if (_YO_LOCAL / "model.bin").exists() else "small"
MODELS = {
    "en": os.environ.get("OVAMHA_ASR_EN", "small"),
    "yo": os.environ.get("OVAMHA_ASR_YO", _YO_DEFAULT),
    "kri": os.environ.get("OVAMHA_ASR_KRI", "small"),
}
# Whisper language code used for decoding.
DECODE_LANG = {"en": "en", "yo": "yo", "kri": "en"}
FALLBACK_NOTE = {
    "kri": "Krio: Whisper has no Krio model; decoded as English (fallback). MMS/DONDO pending.",
    "yo": ("Yoruba: Yoruba fine-tuned Whisper small (see ml/eval/results/yoruba-asr-fleurs.txt)."
           if MODELS["yo"] != "small" else "Yoruba: base Whisper small (weak on Yoruba); Yoruba model not installed."),
}


@dataclass
class AsrResult:
    text: str
    model: str
    ok: bool
    message: str = ""


def model_name(lang: str) -> str:
    m = MODELS.get(lang, "small")
    label = "openai/whisper-small" if m == "small" else ("LyngualLabs/whisper-small-yoruba" if "yoruba" in m else m)
    return f"faster-whisper {label} (CTranslate2 int8)"


@lru_cache(maxsize=3)
def _load(name: str):
    from faster_whisper import WhisperModel

    return WhisperModel(name, device="cpu", compute_type="int8")


def quality_gate(audio: np.ndarray) -> str | None:
    """Return a reason to repeat the recording, or None if it is usable."""
    secs = len(audio) / SAMPLE_RATE
    if secs < 1.0:
        return "Recording too short. Please repeat."
    if secs > 120:
        return "Recording too long (over 2 minutes). Please record a shorter description."
    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    if peak < 0.02:
        return "Too quiet: no speech heard. Please move closer and repeat."
    clipped = float(np.mean(np.abs(audio) > 0.99))
    if clipped > 0.01:
        return "Audio is clipping (too loud). Please hold the phone further away and repeat."
    return None


def latin_share(text: str) -> float:
    """Share of letters that are Latin script (Yoruba and Krio letters such as ẹ, ọ, ɔ, ɛ count)."""
    letters = [c for c in unicodedata.normalize("NFD", text) if c.isalpha()]
    if not letters:
        return 1.0
    return sum(unicodedata.name(c, "").startswith("LATIN") for c in letters) / len(letters)


def transcribe(path: str, lang: str = "en") -> AsrResult:
    from faster_whisper.audio import decode_audio

    name = model_name(lang)
    audio = decode_audio(path, sampling_rate=SAMPLE_RATE)  # 16 kHz mono
    problem = quality_gate(audio)
    if problem:
        return AsrResult("", name, False, problem)
    model = _load(MODELS.get(lang, "small"))
    # Few temperature retries and no conditioning on earlier text: a model that is weak in this
    # language otherwise loops and retries for minutes on a short clip.
    segments, _info = model.transcribe(audio, language=DECODE_LANG.get(lang, "en"), beam_size=5, vad_filter=True,
                                       temperature=(0.0, 0.4), condition_on_previous_text=False)
    text = " ".join(s.text.strip() for s in segments).strip()
    if not text:
        return AsrResult("", name, False, "No speech recognised. Please repeat.")
    if latin_share(text) < 0.8:  # all three languages are written in Latin script
        return AsrResult("", name, False, "The speech was not recognised clearly. Please repeat, or type the description.")
    return AsrResult(text, name, True, FALLBACK_NOTE.get(lang, ""))
