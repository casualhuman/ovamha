#!/usr/bin/env bash
# Download LyngualLabs/whisper-small-yoruba (Apache 2.0) and convert it to CTranslate2 int8 for faster-whisper.
# The repo has no tokenizer.json, so it is generated from the model's own tokenizer files first.
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
from transformers import WhisperTokenizerFast
d = snapshot_download("LyngualLabs/whisper-small-yoruba", local_dir="ml/models/whisper-small-yoruba-hf",
                      ignore_patterns=["runs/*", "training_args.bin"])
WhisperTokenizerFast.from_pretrained(d).save_pretrained(d)
PY
.venv/bin/ct2-transformers-converter --model ml/models/whisper-small-yoruba-hf \
  --output_dir ml/models/whisper-small-yoruba-ct2 --quantization int8 --copy_files tokenizer.json preprocessor_config.json --force
