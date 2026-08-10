from core.generator import Generator
from models.generation_request import GenerationRequest


class VideoService:

    def __init__(self):

        self.generator = Generator()

    def generate(
        self,
        request
    ):
        return self.generator.generate_video(request)