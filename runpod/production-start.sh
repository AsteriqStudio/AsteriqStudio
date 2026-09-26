#!/bin/bash
set -euo pipefail

# The image never embeds model weights.  The first Serverless worker warms the
# shared network volume under a lock; later workers only verify those files.
# This never submits a generation job.
# Serverless templates can mount the attached Network Volume at either path.
# Keep Asteriq's canonical path while also supporting the existing endpoint,
# whose volume is mounted at /workspace.
if [ -d /runpod-volume ]; then
  export ASTERIQ_VOLUME_ROOT="/runpod-volume"
elif [ -d /workspace ]; then
  export ASTERIQ_VOLUME_ROOT="/workspace"
  ln -sfn /workspace /runpod-volume
else
  echo "Asteriq startup error: no Serverless network volume mount found." >&2
  exit 78
fi

export ASTERIQ_MODEL_ROOT="$ASTERIQ_VOLUME_ROOT/models"
mkdir -p "$ASTERIQ_MODEL_ROOT"/{checkpoints,diffusion_models,text_encoders,clip_vision,vae,sam2,upscale,voice,loras,latent_upscale_models}

python3 /opt/asteriq/audit-network-volume.py
python3 /opt/asteriq/bootstrap-model-cache.py
python3 /opt/asteriq/validate-source-video-workflow.py
python3 /opt/asteriq/validate-wan-source-workflow.py

exec /start.sh
