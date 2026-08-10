from backends.comfy_client import ComfyClient

client = ComfyClient()

print(client.is_running())