import torch
from diffusers import DiffusionPipeline
from pathlib import Path

Path("outputs").mkdir(exist_ok=True)

print("Loading model... (first run may take several minutes)")

pipe = DiffusionPipeline.from_pretrained(
    "stabilityai/sdxl-turbo",
    torch_dtype=torch.float32,
)

pipe = pipe.to("cpu")

print("Generating image...")

image = pipe(
    prompt="A cinematic futuristic city at sunset, ultra realistic, volumetric lighting, masterpiece",
    num_inference_steps=2,
    guidance_scale=0.0,
).images[0]

output_path = "outputs/test.png"
image.save(output_path)

print(f"Done! Image saved to {output_path}")