from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import QThread

from ui.left_panel import LeftPanel
from ui.right_panel import RightPanel

from controllers.image_controller import ImageController
from workers.generation_worker import GenerationWorker


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("CineForge AI")

        self.resize(1400, 800)

        self.controller = ImageController()

        self.left = LeftPanel()
        self.right = RightPanel()

        layout = QHBoxLayout()

        layout.addWidget(self.left, 1)
        layout.addWidget(self.right, 2)

        self.setLayout(layout)

        self.left.generate_requested.connect(self.generate_image)

    def generate_image(self, prompt):

        self.right.status.setText("Generating image...")
        self.right.progress.show()

        self.thread = QThread()

        self.worker = GenerationWorker(
            self.controller,
            prompt
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.finished.connect(self.image_finished)

        self.worker.finished.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)

        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def image_finished(self, image_path):

        self.right.display_image(image_path)

        self.right.progress.hide()

        self.right.status.setText("Ready")