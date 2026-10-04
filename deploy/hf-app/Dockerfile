# Ovamha hosted demo (Hugging Face Space). Same code as the offline hub; models are baked into the
# image and loaded with HF_HUB_OFFLINE=1, so the running app calls no external AI service.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH HF_HOME=/home/user/.cache/huggingface PIP_NO_CACHE_DIR=1
WORKDIR /home/user/app

RUN pip install --user torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --user fastapi "uvicorn[standard]" python-multipart "faster-whisper==1.2.1" "av>=11,<16" "fhir.resources==8.3.0" numpy scipy transformers

# Speech recognition (Whisper small, CTranslate2 int8) and read-aloud voices (MMS-TTS English, Yoruba, Krio)
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
RUN python -c "from transformers import VitsModel, AutoTokenizer; [(VitsModel.from_pretrained(f'facebook/mms-tts-{l}'), AutoTokenizer.from_pretrained(f'facebook/mms-tts-{l}')) for l in ('eng', 'yor', 'kri')]"

COPY --chown=user apps/prototype/src apps/prototype/src
COPY --chown=user apps/prototype/web apps/prototype/web
COPY --chown=user content content

ENV HF_HUB_OFFLINE=1 \
    OVAMHA_HOSTED=1 \
    OVAMHA_DATA=/tmp/ovamha \
    OVAMHA_OUTBOX=/tmp/ovamha/outbox \
    FHIR_BASE=https://r8086-ovamha-fhir.hf.space/fhir \
    PYTHONPATH=/home/user/app/apps/prototype/src
EXPOSE 7860
CMD ["python", "-m", "uvicorn", "ovamha_proto.server:app", "--host", "0.0.0.0", "--port", "7860"]
