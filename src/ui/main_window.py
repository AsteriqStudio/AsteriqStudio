from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import QThread

from controllers.image_controller import ImageController
from controllers.video_controller import VideoController

from workers.generation_worker import GenerationWorker

from ui.shell.app_shell import AppShell

from config.app_info import APP_NAME

from pathlib import Path


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        print("MainWindow created")

        self.setWindowTitle(APP_NAME)

        self.resize(1400, 800)

        self.controller = ImageController()

        self.video_controller = VideoController()

        self.shell = AppShell()

        layout = QHBoxLayout()

        layout.addWidget(self.shell)

        self.setLayout(layout)

        self.shell.workspace.prompt.generate_requested.connect(
            self.generate_image
        )

        self.shell.workspace.assets.asset_selected.connect(
            self.show_asset
        )

        self.shell.workspace.video.generate_requested.connect(
            self.generate_video
        )

    def generate_image(self, request):

        print("=" * 50)
        print("MAIN WINDOW")
        print("=" * 50)
        print("Request Type:", type(request))
        print(request)

        self.shell.right.status.setText("Generating image...")
        self.shell.right.progress.show()

        self.thread = QThread()

        self.worker = GenerationWorker(
            self.controller,
            request
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.finished.connect(
            self.image_finished
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.start()

    def image_finished(self, image_path):

        self.shell.right.display_image(image_path)

        self.shell.workspace.assets.refresh()

        self.shell.right.progress.hide()

        self.shell.right.status.setText("Ready")

    def show_asset(self, path):

        extension = Path(path).suffix.lower()

        if extension in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:

            self.shell.right.display_image(path)

            self.shell.workspace.video.set_image(path)

            self.shell.right.status.setText(
                "Viewing image"
            )

        elif extension in [
            ".mp4",
            ".mov",
            ".avi",
            ".mkv"
        ]:

            self.shell.right.display_video(path)

            self.shell.right.status.setText(
                "Viewing video"
            )

        elif extension in [
            ".mp3",
            ".wav",
            ".ogg"
        ]:

            print("Play audio:", path)

            self.shell.right.status.setText(
                "Playing audio"
            )

    def generate_video(self, request):

        print("=" * 50)
        print("VIDEO REQUEST")
        print("=" * 50)
        print(request)

        self.shell.right.status.setText(
            "Generating video..."
        )

        self.shell.right.progress.show()

        video_path = self.video_controller.generate(
            request
        )

        self.shell.right.progress.hide()

        self.shell.right.status.setText(
            "Video generation finished."
        )