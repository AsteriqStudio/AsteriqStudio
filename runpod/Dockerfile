FROM runpod/worker-comfyui:5.8.6-base

USER root

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg git curl blender espeak-ng libsndfile1 libgl1 python3-venv \
 && rm -rf /var/lib/apt/lists/*

# The ComfyUI base image supplies the Wan VACE core operators. These external
# nodes provide video I/O and segmentation; their model weights stay on the
# network volume and are never downloaded during image build.
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite \
 && git clone --depth 1 https://github.com/kijai/ComfyUI-segment-anything-2.git /comfyui/custom_nodes/ComfyUI-segment-anything-2

# Do not install the complete ControlNet Auxiliary preprocessor bundle: it
# attempts to replace ComfyUI's CUDA torch stack and makes reproducible image
# builds fail.  Asteriq uses the separate, pinned MediaPipe runtime for pose
# capture and needs only video I/O here.
RUN pip install --no-cache-dir opencv-python-headless imageio-ffmpeg

# The voice/transcription stack runs in a separate Serverless stage, so its
# dependency set cannot replace the CUDA packages used by this video worker.
RUN pip install --no-cache-dir 'huggingface_hub>=0.24'

COPY runpod/extra_model_paths.yaml /comfyui/extra_model_paths.yaml
COPY runpod/production-stack.json /opt/asteriq/production-stack.json
COPY runpod/model-cache-manifest.json /opt/asteriq/model-cache-manifest.json
COPY runpod/audit-network-volume.py /opt/asteriq/audit-network-volume.py
COPY runpod/source-video-workflow-manifest.json /opt/asteriq/source-video-workflow-manifest.json
COPY runpod/bootstrap-model-cache.py /opt/asteriq/bootstrap-model-cache.py
COPY runpod/validate-source-video-workflow.py /opt/asteriq/validate-source-video-workflow.py
COPY runpod/preflight-source-video.py /opt/asteriq/preflight-source-video.py
COPY runpod/production-start.sh /opt/asteriq/production-start.sh
RUN chmod +x /opt/asteriq/production-start.sh /opt/asteriq/audit-network-volume.py /opt/asteriq/bootstrap-model-cache.py /opt/asteriq/validate-source-video-workflow.py /opt/asteriq/preflight-source-video.py

# The first release after this change warms the shared RunPod network volume.
# The bootstrap uses a cross-worker lock and is idempotent, so later worker
# starts only validate the cache instead of re-downloading the weights.
ENV ASTERIQ_MODEL_CACHE_BOOTSTRAP=1
ENV ASTERIQ_MODEL_CACHE_INTEGRITY=sha256_shared_volume_lock

CMD ["/opt/asteriq/production-start.sh"]
