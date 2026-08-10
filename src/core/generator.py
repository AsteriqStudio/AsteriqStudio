from backends.comfy_backend import ComfyBackend
from models.generation_request import GenerationRequest


class Generator:

    def __init__(self):
        self.backend = None

    def load_backend(self):
        if self.backend is None:

            print("=" * 50)
            print("LOADING BACKEND")
            print("=" * 50)

            self.backend = ComfyBackend()

    def set_backend(self, backend):
        self.backend = backend

    def health_check(self):
        self.load_backend()
        return self.backend.health_check()

    def available_models(self):
        self.load_backend()
        return self.backend.available_models()

    def generate_image(
        self,
        request: GenerationRequest
    ):

        self.load_backend()

        return self.backend.generate_image(request)

    def generate_video(self, request):

        self.load_backend()

        return self.backend.generate_video(request)