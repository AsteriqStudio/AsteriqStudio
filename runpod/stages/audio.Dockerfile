# Transformers refuses to load PyTorch checkpoints with torch < 2.6 because
# of CVE-2025-32434.  Keep the audio worker on a patched CUDA-compatible base
# so the cached translation models can be loaded without weakening that guard.
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

WORKDIR /opt/asteriq
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg git espeak-ng libsndfile1 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/myshell-ai/OpenVoice.git /opt/openvoice \
 && pip install --no-cache-dir "runpod>=1.7,<2" "faster-whisper>=1.1,<2" "librosa>=0.10,<0.11" "pydub>=0.25,<1" "eng_to_ipa==0.0.2" "inflect>=7,<8" "Unidecode>=1.3,<2" "pypinyin>=0.50,<1" "cn2an>=0.5,<1" "jieba>=0.42,<1" "langid>=1.1,<2" "transformers>=4.46,<5" "sentencepiece>=0.2,<1"
COPY runpod/stages/handler.py /opt/asteriq/handler.py
COPY runpod/stages/stage-cache-manifest.json /opt/asteriq/stage-cache-manifest.json
COPY runpod/stages/bootstrap-stage-cache.py /opt/asteriq/bootstrap-stage-cache.py
ENV ASTERIQ_STAGE=audio ASTERIQ_VOLUME_ROOT=/runpod-volume PYTHONUNBUFFERED=1
CMD ["python", "-u", "/opt/asteriq/handler.py"]
