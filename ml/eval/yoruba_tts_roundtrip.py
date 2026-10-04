"""Yoruba read-aloud intelligibility proxy: Yoruba text -> MMS-TTS Yoruba voice -> Yoruba ASR -> text.

If the Yoruba speech model recovers the sentence from the synthetic voice, the voice is at least
machine-intelligible. This is a proxy only; a native speaker listening is the real test.
Sentences: first N FLEURS yo_ng test transcriptions (CC-BY 4.0). All offline.

    .venv/bin/python ml/eval/yoruba_tts_roundtrip.py [N]
"""
import sys
import time
from pathlib import Path

import jiwer
import numpy as np
import pandas as pd
import torch
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, VitsModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yoruba_asr_eval import DATA, ROOT, norm  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20


def main() -> None:
    refs = list(pd.read_parquet(DATA, columns=["transcription"]).head(N)["transcription"])
    tok = AutoTokenizer.from_pretrained("facebook/mms-tts-yor")
    tts = VitsModel.from_pretrained("facebook/mms-tts-yor")
    asr = WhisperModel(str(ROOT / "ml/models/whisper-small-yoruba-ct2"), device="cpu", compute_type="int8")
    hyps, t0 = [], time.time()
    for r in refs:
        with torch.no_grad():
            wav = tts(**tok(r, return_tensors="pt")).waveform[0].numpy()
        sr = tts.config.sampling_rate
        idx = np.linspace(0, len(wav) - 1, int(len(wav) * 16000 / sr))
        a = np.interp(idx, np.arange(len(wav)), wav).astype("float32")
        segs, _ = asr.transcribe(a, language="yo", beam_size=5)
        hyps.append(" ".join(s.text.strip() for s in segs))
    w = jiwer.wer([norm(x) for x in refs], [norm(h) for h in hyps])
    w_nt = jiwer.wer([norm(x, False) for x in refs], [norm(h, False) for h in hyps])
    lines = [f"Yoruba read-aloud round trip on {N} FLEURS sentences: MMS-TTS Yoruba voice -> whisper-small-yoruba.",
             f"WER {w:.1%}   WER ignoring tone marks {w_nt:.1%}   ({time.time() - t0:.0f} s total)",
             "Proxy for intelligibility only; a native-speaker listening test is still needed.", ""]
    for r, h in list(zip(refs, hyps))[:3]:
        lines += [f"  TEXT : {r}", f"  HEARD: {h}", ""]
    out = ROOT / "ml/eval/results/yoruba-tts-roundtrip.txt"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
