from pathlib import Path


class ModelManager:

    def __init__(self):

        self.model_directory = Path("models")

        self.model_directory.mkdir(exist_ok=True)

    def model_exists(self, model_name):

        return (self.model_directory / model_name).exists()

    def get_model_path(self, model_name):

        return self.model_directory / model_name

    def load(self, model_name):

        print(f"Loading {model_name}")

        if not self.model_exists(model_name):

            print("Model not downloaded yet.")

            return None

        print("Model found.")

        return self.get_model_path(model_name)