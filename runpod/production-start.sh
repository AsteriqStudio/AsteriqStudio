#!/bin/bash
set -euo pipefail

# The worker image is safe to boot before model installation. This script only
# checks the shared cache and starts ComfyUI; it does not download a model or
# submit a generation. A separate operator-start command controls bootstrap
# and the first production run.
MODEL_ROOT="/runpod-volume/models"
mkdir -p "$MODEL_ROOT"/{checkpoints,text_encoders,sam2,upscale,voice}

for required in \
  "$MODEL_ROOT/checkpoints/ltx-video-2b-v0.9.5.safetensors" \
  "$MODEL_ROOT/text_encoders/t5xxl_fp16.safetensors"; do
  if [ ! -f "$required" ]; then
    echo "Asteriq model cache waiting: $required"
  fi
done

exec /start.sh
