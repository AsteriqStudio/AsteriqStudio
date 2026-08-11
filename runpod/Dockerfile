FROM runpod/worker-comfyui:5.8.6-base

RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git /comfyui/custom_nodes/ComfyUI-LTXVideo

RUN cd /comfyui/custom_nodes/ComfyUI-LTXVideo && git checkout aceeae9635f6d493f2893ba3c411a1c36031788a

RUN pip install -r /comfyui/custom_nodes/ComfyUI-LTXVideo/requirements.txt
