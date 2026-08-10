from managers.config_manager import ConfigManager

settings = ConfigManager.load()

print(settings)

settings.width = 1024

settings.height = 1024

ConfigManager.save(settings)

print("Saved!")