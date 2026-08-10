from PySide6.QtCore import QObject, Signal

from models.generation_request import GenerationRequest


class GenerationWorker(QObject):

    finished = Signal(str)
    status = Signal(str)

    def __init__(
        self,
        controller,
        request: GenerationRequest
    ):
        super().__init__()

        self.controller = controller
        self.request = request

    def run(self):

        self.status.emit("Generating image...")

        image_path = self.controller.generate(
            self.request
        )

        self.finished.emit(image_path)