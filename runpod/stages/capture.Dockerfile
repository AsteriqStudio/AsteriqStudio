FROM python:3.11-slim

WORKDIR /opt/asteriq
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "runpod>=1.7,<2" "opencv-python-headless>=4.10,<5" "mediapipe>=0.10,<1"
COPY runpod/stages/handler.py /opt/asteriq/handler.py
COPY runpod/stages/stage-cache-manifest.json /opt/asteriq/stage-cache-manifest.json
COPY runpod/stages/bootstrap-stage-cache.py /opt/asteriq/bootstrap-stage-cache.py
ENV ASTERIQ_STAGE=capture ASTERIQ_VOLUME_ROOT=/runpod-volume PYTHONUNBUFFERED=1
CMD ["python", "-u", "/opt/asteriq/handler.py"]
