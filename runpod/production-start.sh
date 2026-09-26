#!/bin/bash
set -euo pipefail

# The image never embeds model weights.  The first Serverless worker warms the
# shared network volume under a lock; later workers only verify those files.
# This never submits a generation job.
MODEL_ROOT="/runpod-volume/models"
mkdir -p "$MODEL_ROOT"/{checkpoints,text_encoders,sam2,upscale,voice,loras,latent_upscale_models}

python3 /opt/asteriq/audit-network-volume.py
python3 /opt/asteriq/bootstrap-model-cache.py
python3 /opt/asteriq/validate-source-video-workflow.py

exec /start.sh
