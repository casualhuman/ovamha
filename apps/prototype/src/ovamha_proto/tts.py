"""Read-back audio, offline.

1. Pre-recorded clips (preferred, especially for Krio and Yoruba):
   content/audio/<lang>/<field>.wav, plus yes.wav / no.wav. Audio is never committed.
2. Otherwise the system's offline voice: macOS `say` on a laptop, `espeak-ng` on a Pi.
   This speaks English; for Krio/Yoruba it is a labelled fallback until clips or
   MMS-TTS (P2) are added.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

CLIPS = Path(__file__).resolve().parents[4] / "content" / "audio"


def _concat(paths: list[Path], out: Path) -> bool:
    try:
        with wave.open(str(paths[0])) as w0:
            params = w0.getparams()
        with wave.open(str(out), "wb") as dst:
            dst.setparams(params)
            for p in paths:
                with wave.open(str(p)) as w:
                    if w.getparams()[:3] != params[:3]:
                        return False
                    dst.writeframes(w.readframes(w.getnframes()))
        return True
    except (wave.Error, OSError):
        return False


def _clips(items: list[tuple[str, str]], lang: str) -> list[Path] | None:
    d = CLIPS / lang
    paths = []
    for f, v in items:
        a, b = d / f"{f}.wav", d / f"{v.lower()}.wav"
        if not (a.exists() and b.exists()):
            return None
        paths += [a, b]
    return paths


def readback_audio(items: list[tuple[str, str, str]], lang: str) -> tuple[str | None, str]:
    """items: (field, spoken label, spoken value). Returns (wav path or None, note)."""
    out = Path(tempfile.mkdtemp()) / "readback.wav"
    clips = _clips([(f, v) for f, _, v in items], lang)
    if clips and _concat(clips, out):
        return str(out), "Pre-recorded read-back clips"
    text = "Please confirm. " + ". ".join(f"{lab}: {val}" for _, lab, val in items) + "."
    note = "" if lang == "en" else " (spoken in English: Krio/Yoruba clips not recorded yet)"
    if shutil.which("say"):
        aiff = out.with_suffix(".aiff")
        subprocess.run(["say", "-o", str(aiff), text], check=True, timeout=60)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", str(aiff), str(out)], check=True, timeout=60)
        return str(out), "Offline system voice (macOS say)" + note
    if shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-w", str(out), text], check=True, timeout=60)
        return str(out), "Offline system voice (espeak-ng)" + note
    return None, "No offline voice available; read the list aloud from the screen."
