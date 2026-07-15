from services.image_service import ImageService


class ImageController:

    def __init__(self):

        self.image_service = ImageService()

    def generate(self, prompt):

        return self.image_service.generate(prompt)