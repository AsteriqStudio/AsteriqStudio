FROM runpod/worker-comfyui:5.8.6-base

USER root

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg git \
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
COPY runpod/production-start.sh /opt/asteriq/production-start.sh
RUN chmod +x /opt/asteriq/production-start.sh

CMD ["/opt/asteriq/production-start.sh"]
