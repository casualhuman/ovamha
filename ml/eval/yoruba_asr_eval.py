"""Yoruba speech recognition: base Whisper small vs the Yoruba fine-tuned Whisper small.

Data: Google FLEURS Yoruba (yo_ng) test split, CC-BY 4.0: real Yoruba speech, read Wikipedia
sentences (general domain, not clinical). First N utterances, fixed order, so the run is
reproducible. Models run offline with faster-whisper (CTranslate2 int8), as in the app.

    .venv/bin/python ml/eval/yoruba_asr_eval.py [N]

Download the data first (not committed):
    hf_hub_download("google/fleurs", "parquet-data/yo_ng/test-00000-of-00001.parquet",
                    repo_type="dataset", local_dir="data/eval/fleurs")
"""
import io
import re
import sys
import time
import unicodedata
from pathlib import Path

import jiwer
import numpy as np
import pandas as pd
import soundfile as sf
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/eval/fleurs/parquet-data/yo_ng/test-00000-of-00001.parquet"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
MODELS = {
    "base whisper-small (current app)": "small",
    "whisper-small-yoruba (LyngualLabs, fine-tuned)": str(ROOT / "ml/models/whisper-small-yoruba-ct2"),
}


def norm(t: str, tones: bool = True) -> str:
    t = unicodedata.normalize("NFC", t.lower())
    if not tones:
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def audio(row) -> np.ndarray:
    a, sr = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    if sr != 16000:
        idx = np.linspace(0, len(a) - 1, int(len(a) * 16000 / sr))
        a = np.interp(idx, np.arange(len(a)), a).astype("float32")
    return a


def main() -> None:
    df = pd.read_parquet(DATA).head(N)
    refs = [r for r in df["transcription"]]
    clips = [audio(r) for _, r in df.iterrows()]
    secs = sum(len(c) for c in clips) / 16000
    lines = [f"Yoruba ASR on Google FLEURS yo_ng test (CC-BY 4.0): first {len(df)} utterances, {secs / 60:.1f} minutes of audio.",
             "General-domain read speech (Wikipedia sentences), not clinical. Offline, CPU, int8.", ""]
    examples = []
    for name, path in MODELS.items():
        m = WhisperModel(path, device="cpu", compute_type="int8")
        t0, hyps = time.time(), []
        for a in clips:
            segs, _ = m.transcribe(a, language="yo", beam_size=5, vad_filter=False)
            hyps.append(" ".join(s.text.strip() for s in segs))
        dt = time.time() - t0
        w = jiwer.wer([norm(r) for r in refs], [norm(h) for h in hyps])
        c = jiwer.cer([norm(r) for r in refs], [norm(h) for h in hyps])
        w_nt = jiwer.wer([norm(r, False) for r in refs], [norm(h, False) for h in hyps])
        lines.append(f"{name:50} WER {w:6.1%}   CER {c:6.1%}   WER ignoring tone marks {w_nt:6.1%}   ({dt / secs:.2f}x real time)")
        examples.append((name, hyps[:3]))
    lines += ["", "Examples (reference, then each model):"]
    for i in range(3):
        lines.append(f"  REF: {refs[i]}")
        for name, hyps in examples:
            lines.append(f"  {name.split(' (')[0]:28}: {hyps[i]}")
        lines.append("")
    out = ROOT / "ml/eval/results/yoruba-asr-fleurs.txt"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
