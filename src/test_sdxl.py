import torch
from diffusers import AutoPipelineForText2Image

print("Loading model...")

pipeline = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sdxl-turbo",
    torch_dtype=torch.float32
)

pipeline.to("cpu")

print("Generating...")

image = pipeline(
    "A cinematic futuristic city at sunset, ultra realistic, volumetric lighting",
    num_inference_steps=2,
    guidance_scale=0.0
).images[0]

image.save("outputs/test.png")

print("Done!")