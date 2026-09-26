FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /opt/asteriq
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends blender ffmpeg git libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
# TRELLIS and its heavyweight GPU extensions stay outside the video worker.
# Source is present for reproducible installation; model files remain on the
# mounted cache and are never baked into the public container image.
RUN git clone --depth 1 --recurse-submodules https://github.com/microsoft/TRELLIS.git /opt/TRELLIS \
 && pip install --no-cache-dir "runpod>=1.7,<2" "huggingface_hub>=0.24"
COPY runpod/stages/handler.py /opt/asteriq/handler.py
ENV ASTERIQ_STAGE=direct_3d ASTERIQ_VOLUME_ROOT=/runpod-volume PYTHONUNBUFFERED=1
CMD ["python", "-u", "/opt/asteriq/handler.py"]
