from pathlib import Path


class ModelManager:

    def __init__(self):

        self.models_folder = Path("Models")

        self.models_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        self.models = {}

    def register(
        self,
        name,
        model_type,
        folder
    ):

        self.models[name] = {

            "type": model_type,

            "folder": self.models_folder / folder

        }

    def get(self, name):

        return self.models.get(name)

    def installed_models(self):

        return list(self.models.keys())