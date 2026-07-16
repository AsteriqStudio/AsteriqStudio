import json
from pathlib import Path

from settings.generation_settings import GenerationSettings


class ConfigManager:

    CONFIG = Path("Config/settings.json")

    @staticmethod
    def load():

        if not ConfigManager.CONFIG.exists():

            return GenerationSettings()

        with open(ConfigManager.CONFIG) as f:

            data = json.load(f)

        return GenerationSettings(**data)

    @staticmethod
    def save(settings):

        ConfigManager.CONFIG.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(ConfigManager.CONFIG, "w") as f:

            json.dump(
                settings.__dict__,
                f,
                indent=4
            )