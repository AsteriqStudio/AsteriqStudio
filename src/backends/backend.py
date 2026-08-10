from abc import ABC, abstractmethod

from models.generation_request import GenerationRequest


class Backend(ABC):

    @abstractmethod
    def generate_image(
        self,
        request: GenerationRequest
    ):
        pass

    @abstractmethod
    def generate_video(self, request):
        pass

    @abstractmethod
    def health_check(self):
        pass

    @abstractmethod
    def available_models(self):
        pass