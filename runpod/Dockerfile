FROM runpod/worker-comfyui:5.8.6-base

USER root

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg git curl \
 && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git /comfyui/custom_nodes/ComfyUI-LTXVideo

RUN cd /comfyui/custom_nodes/ComfyUI-LTXVideo && git checkout aceeae9635f6d493f2893ba3c411a1c36031788a

RUN pip install -r /comfyui/custom_nodes/ComfyUI-LTXVideo/requirements.txt

# These nodes provide the video IO, segmentation, and pose-control interfaces
# used by the Asteriq production plan. Model weights stay on the network volume
# and are not downloaded during image build.
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite \
 && git clone --depth 1 https://github.com/kijai/ComfyUI-segment-anything-2.git /comfyui/custom_nodes/ComfyUI-segment-anything-2 \
 && git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git /comfyui/custom_nodes/comfyui_controlnet_aux

# VideoHelperSuite and controlnet_aux publish dependency files. The SAM2 node
# uses the base ComfyUI environment and does not include one, so installing a
# hard-coded missing path makes the whole Serverless image fail to build.
RUN pip install -r /comfyui/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt \
 && pip install -r /comfyui/custom_nodes/comfyui_controlnet_aux/requirements.txt

COPY runpod/extra_model_paths.yaml /comfyui/extra_model_paths.yaml
COPY runpod/production-stack.json /opt/asteriq/production-stack.json
COPY runpod/model-cache-manifest.json /opt/asteriq/model-cache-manifest.json
COPY runpod/bootstrap-model-cache.py /opt/asteriq/bootstrap-model-cache.py
COPY runpod/production-start.sh /opt/asteriq/production-start.sh
RUN chmod +x /opt/asteriq/production-start.sh /opt/asteriq/bootstrap-model-cache.py

# The first release after this change warms the shared RunPod network volume.
# The bootstrap uses a cross-worker lock and is idempotent, so later worker
# starts only validate the cache instead of re-downloading the weights.
ENV ASTERIQ_MODEL_CACHE_BOOTSTRAP=1
ENV ASTERIQ_MODEL_CACHE_INTEGRITY=sha256_shared_volume_lock

CMD ["/opt/asteriq/production-start.sh"]
