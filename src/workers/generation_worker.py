from PySide6.QtCore import QObject, Signal


class GenerationWorker(QObject):

    finished = Signal(str)
    status = Signal(str)

    def __init__(self, controller, prompt):
        super().__init__()

        self.controller = controller
        self.prompt = prompt

    def run(self):

        self.status.emit("Generating image...")

        image_path = self.controller.generate(self.prompt)

        self.finished.emit(image_path)