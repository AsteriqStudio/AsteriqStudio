from models.registry import ModelRegistry


class Generator:

    def __init__(self):
        self.model = None

    def generate(self, prompt):

        if self.model is None:
            print("Loading model for the first time...")

            self.model = ModelRegistry.get_model("SDXL Turbo")

        return self.model.generate(prompt)