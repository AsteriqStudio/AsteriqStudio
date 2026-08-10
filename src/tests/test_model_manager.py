from managers.model_manager import ModelManager

mm = ModelManager()

mm.register(
    "SDXL Turbo",
    "image",
    "sdxl"
)

mm.register(
    "LTX Video",
    "video",
    "ltx"
)

print(mm.installed_models())

print(mm.get("SDXL Turbo"))