import time

from models.base_model import BaseModel


class DummyModel(BaseModel):

    def generate(self, prompt: str):

        print("Loading model...")
        time.sleep(1)

        print("Generating image...")
        time.sleep(2)

        print("Saving...")
        time.sleep(1)

        return "Finished"