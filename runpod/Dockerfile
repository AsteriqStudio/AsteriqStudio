FROM runpod/worker-comfyui:5.8.6

RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git /workspace/runpod-slim/ComfyUI/custom_nodes/ComfyUI-LTXVideo

RUN cd /workspace/runpod-slim/ComfyUI/custom_nodes/ComfyUI-LTXVideo && git checkout aceeae9635f6d493f2893ba3c411a1c36031788a

RUN pip install -r /workspace/runpod-slim/ComfyUI/custom_nodes/ComfyUI-LTXVideo/requirements.txt

COPY runpod/extra_model_paths.yaml /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml
