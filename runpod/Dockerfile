FROM runpod/worker-comfyui:5.8.6-base

USER root

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg git curl blender espeak-ng libsndfile1 libgl1 python3-venv \
 && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git /comfyui/custom_nodes/ComfyUI-LTXVideo

RUN cd /comfyui/custom_nodes/ComfyUI-LTXVideo && git checkout aceeae9635f6d493f2893ba3c411a1c36031788a

RUN pip install -r /comfyui/custom_nodes/ComfyUI-LTXVideo/requirements.txt

# These nodes provide the video IO, segmentation, and pose-control interfaces
# used by the Asteriq production plan. Model weights stay on the network volume
# and are not downloaded during image build.
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite \
 && git clone --depth 1 https://github.com/kijai/ComfyUI-segment-anything-2.git /comfyui/custom_nodes/ComfyUI-segment-anything-2

# Do not install the complete ControlNet Auxiliary preprocessor bundle: it
# attempts to replace ComfyUI's CUDA torch stack and makes reproducible image
# builds fail.  Asteriq uses the separate, pinned MediaPipe runtime for pose
# capture and needs only video I/O here.
RUN pip install --no-cache-dir opencv-python-headless imageio-ffmpeg

# Keep voice/transcription packages separate from the ComfyUI interpreter.
# No model API SDK is installed; all weights are cached from public repos on
# the attached RunPod volume at worker boot.
RUN git clone https://github.com/myshell-ai/OpenVoice.git /opt/asteriq/openvoice \
 && cd /opt/asteriq/openvoice && git checkout 74a1d147b17a8c3092dd5430504bd83ef6c7eb23 \
 && python3 -m venv --system-site-packages /opt/asteriq/audio-venv
COPY runpod/audio-requirements.txt /opt/asteriq/audio-requirements.txt
RUN /opt/asteriq/audio-venv/bin/pip install --no-cache-dir -r /opt/asteriq/audio-requirements.txt \
 && pip install --no-cache-dir 'huggingface_hub>=0.24'

COPY runpod/extra_model_paths.yaml /comfyui/extra_model_paths.yaml
COPY runpod/production-stack.json /opt/asteriq/production-stack.json
COPY runpod/audio-requirements.txt /opt/asteriq/audio-requirements.txt
COPY runpod/model-cache-manifest.json /opt/asteriq/model-cache-manifest.json
COPY runpod/audit-network-volume.py /opt/asteriq/audit-network-volume.py
COPY runpod/source-video-workflow-manifest.json /opt/asteriq/source-video-workflow-manifest.json
COPY runpod/bootstrap-model-cache.py /opt/asteriq/bootstrap-model-cache.py
COPY runpod/validate-source-video-workflow.py /opt/asteriq/validate-source-video-workflow.py
COPY runpod/production-start.sh /opt/asteriq/production-start.sh
RUN chmod +x /opt/asteriq/production-start.sh /opt/asteriq/audit-network-volume.py /opt/asteriq/bootstrap-model-cache.py /opt/asteriq/validate-source-video-workflow.py

# The first release after this change warms the shared RunPod network volume.
# The bootstrap uses a cross-worker lock and is idempotent, so later worker
# starts only validate the cache instead of re-downloading the weights.
ENV ASTERIQ_MODEL_CACHE_BOOTSTRAP=1
ENV ASTERIQ_MODEL_CACHE_INTEGRITY=sha256_shared_volume_lock

CMD ["/opt/asteriq/production-start.sh"]
