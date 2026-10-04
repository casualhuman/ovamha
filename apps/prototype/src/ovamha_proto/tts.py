"""Offline read-aloud in English, Krio and Yoruba.

Voices, in order of preference:
1. Pre-recorded clips by native speakers: content/audio/<lang>/<key>.wav (best; never committed).
2. MMS-TTS (facebook/mms-tts-eng / -yor / -kri, CC-BY-NC 4.0) via transformers, once downloaded.
3. The system's offline voice (macOS `say`, `espeak-ng`), English only.

Wording comes from content/readback/phrases.json. Krio and Yoruba wording must be
written by native-speaker health workers; until a phrase is filled in, that item is
spoken in English with the English voice, and the response says so.
"""
from __future__ import annotations

import hashlib
import re
import json
import shutil
import subprocess
import tempfile
import uuid
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CLIPS = ROOT / "content" / "audio"
PHRASES = ROOT / "content" / "readback" / "phrases.json"
CACHE = Path(tempfile.gettempdir()) / "ovamha-tts"
MMS = {"en": "facebook/mms-tts-eng", "yo": "facebook/mms-tts-yor", "kri": "facebook/mms-tts-kri"}

_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_words(n) -> str:
    """English words for 0-999 (MMS voices read letters, not digits)."""
    if isinstance(n, float) and not n.is_integer():
        whole, frac = str(n).split(".")
        return f"{number_words(int(whole))} point {' '.join(_ONES[int(d)] for d in frac)}"
    n = int(n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        rest = n % 100
        return _ONES[n // 100] + " hundred" + ("" if rest == 0 else " and " + number_words(rest))
    return str(n)


@lru_cache(maxsize=1)
def phrases() -> dict:
    return json.loads(PHRASES.read_text()) if PHRASES.exists() else {}


def _phrase(lang: str, group: str, key: str) -> str | None:
    v = phrases().get(lang, {}).get(group, {}).get(str(key))
    return v or None


def item_text(field: str, label: str, value, lang: str) -> tuple[str, str]:
    """Text to speak for one read-back item, and the language it is actually in."""
    if isinstance(value, bool):
        vkey = "yes" if value else "no"
    else:
        vkey = str(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        spoken_val = number_words(value)
        # Numbers are spoken in English words for now: a Yoruba or Krio voice cannot read them.
        return f"{_phrase('en', 'fields', field) or label}: {spoken_val}", "en"
    f, v = _phrase(lang, "fields", field), _phrase(lang, "values", vkey)
    if f and v:
        return f"{f}: {v}", lang
    return f"{_phrase('en', 'fields', field) or label}: {_phrase('en', 'values', vkey) or vkey}", "en"


def text_in(lang: str, key: str, fallback: str) -> tuple[str, str]:
    t = _phrase(lang, "prompts", key)
    return (t, lang) if t else (_phrase("en", "prompts", key) or fallback, "en")


@lru_cache(maxsize=3)
def _mms(lang: str):
    from transformers import AutoTokenizer, VitsModel

    name = MMS[lang]
    # local_files_only: never reach for the internet during an encounter.
    return VitsModel.from_pretrained(name, local_files_only=True), AutoTokenizer.from_pretrained(name, local_files_only=True)


def mms_available(lang: str) -> bool:
    try:
        _mms(lang)
        return True
    except Exception:
        return False


def _speak_mms(text: str, lang: str, out: Path) -> None:
    import numpy as np
    import scipy.io.wavfile
    import torch

    model, tok = _mms(lang)
    inputs = tok(text, return_tensors="pt")
    with torch.no_grad():
        wav = model(**inputs).waveform[0].numpy()
    scipy.io.wavfile.write(out, model.config.sampling_rate, (np.clip(wav, -1, 1) * 32767).astype("int16"))


def speak(text: str, lang: str, clip_key: str | None = None, cache: bool = True) -> tuple[Path | None, str]:
    """Synthesize text in lang. Returns (wav path, voice used).

    cache=False is for text about a particular woman (her transcript, card number, handover): the
    audio goes to a one-off file the caller deletes after sending, so no recording of her details
    stays on disk (architecture DEV-03). Shared wording (questions, prompts, labels) is cached."""
    if clip_key:
        clip = CLIPS / lang / f"{clip_key}.wav"
        if clip.exists():
            return clip, "recorded clip"
    text = re.sub(r"\d+(?:\.\d+)?", lambda m: number_words(float(m.group()) if "." in m.group() else int(m.group())), text)
    CACHE.mkdir(exist_ok=True)
    if cache:
        out = CACHE / (hashlib.sha1(f"{lang}|{text}".encode()).hexdigest() + ".wav")
        if out.exists():
            return out, "cached"
    else:
        out = CACHE / f"once-{uuid.uuid4().hex}.wav"
    if lang in MMS and mms_available(lang):
        _speak_mms(text, lang, out)
        return out, f"MMS-TTS ({MMS[lang]})"
    if shutil.which("say"):
        aiff = out.with_suffix(".aiff")
        subprocess.run(["say", "-o", str(aiff), text], check=True, timeout=60)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", str(aiff), str(out)], check=True, timeout=60)
        aiff.unlink(missing_ok=True)
        return out, "system voice (macOS say)"
    if shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-w", str(out), text], check=True, timeout=60)
        return out, "system voice (espeak-ng)"
    return None, "no offline voice available"
