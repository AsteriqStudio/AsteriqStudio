from services.image_service import ImageService
from models.generation_request import GenerationRequest


class ImageController:

    def __init__(self):

        self.image_service = ImageService()

    def generate(
        self,
        request: GenerationRequest
    ):

        return self.image_service.generate(request)