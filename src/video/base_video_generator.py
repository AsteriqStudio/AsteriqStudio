from abc import ABC, abstractmethod


class BaseVideoGenerator(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
        image_path: str | None = None,
        output_path: str | None = None,
    ):
        pass