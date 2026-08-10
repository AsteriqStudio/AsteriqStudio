from services.model_manager import ModelManager

manager = ModelManager()

print(manager.model_exists("sdxl"))

print(manager.get_model_path("sdxl"))

manager.load("sdxl")