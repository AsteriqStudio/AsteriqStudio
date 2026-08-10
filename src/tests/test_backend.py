from backends.comfy_backend import ComfyBackend

backend = ComfyBackend()

image = backend.generate(
    "A futuristic cyberpunk city at sunset"
)

print(image)