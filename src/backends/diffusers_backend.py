from backends.backend import Backend

from models.sdxl_model import SDXLModel


class DiffusersBackend(Backend):

    def __init__(self):

        self.model = SDXLModel()

    def generate_image(self, prompt):

        return self.model.generate(prompt)

    def generate_video(self, prompt, image_path=None):

        raise NotImplementedError(
            "Video generation not supported."
        )