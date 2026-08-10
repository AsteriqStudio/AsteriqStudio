from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QProgressBar,
    QLineEdit,
)

from PySide6.QtCore import Signal
from torch import layout

from ui.video_preview import VideoPreview
from models.generation_request import GenerationRequest


class VideoPanel(QWidget):

    # image_path, duration(seconds), fps
    generate_requested = Signal(object)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # -----------------------------
        # Title
        # -----------------------------
        layout.addWidget(QLabel("Video Generation"))

        # -----------------------------
        # Selected Image
        # -----------------------------
        layout.addWidget(QLabel("Selected Image"))

        self.image_path = QLineEdit()

       

        self.image_path.setReadOnly(True)

        layout.addWidget(self.image_path)

        # -----------------------------
        # Motion Prompt
        # -----------------------------
        layout.addWidget(QLabel("Motion Prompt"))

        self.video_prompt = QLineEdit()

        self.video_prompt.setPlaceholderText(
            "Describe how the image should move..."
        )

        layout.addWidget(self.video_prompt)

        # -----------------------------
        # Negative Motion Prompt
        # -----------------------------
        layout.addWidget(QLabel("Negative Motion Prompt"))

        self.video_negative_prompt = QLineEdit()

        layout.addWidget(self.video_negative_prompt)

        # -----------------------------
        # Duration
        # -----------------------------
        layout.addWidget(QLabel("Duration"))

        self.duration = QComboBox()
        self.duration.addItems([
            "3 Seconds",
            "5 Seconds",
            "10 Seconds"
        ])

        layout.addWidget(self.duration)

        # -----------------------------
        # FPS
        # -----------------------------
        layout.addWidget(QLabel("Frame Rate"))

        self.fps = QComboBox()
        self.fps.addItems([
            "8 FPS",
            "16 FPS",
            "24 FPS"
        ])

        layout.addWidget(self.fps)

        # -----------------------------
        # Generate Button
        # -----------------------------
        self.generate = QPushButton("Generate Video")

        self.generate.setEnabled(False)

        self.generate.clicked.connect(
            self.generate_clicked
        )

        layout.addWidget(self.generate)
        # -----------------------------
        # Progress Bar
        # -----------------------------
        self.progress = QProgressBar()
        self.progress.hide()

        layout.addWidget(self.progress)

        # -----------------------------
        # Preview
        # -----------------------------
        self.preview = VideoPreview()

        layout.addWidget(self.preview)

        self.setLayout(layout)

    def generate_clicked(self):

        request = GenerationRequest()

        request.image_path = self.image_path.text()

        request.video_prompt = (
            self.video_prompt.text()
        )

        request.video_negative_prompt = (
            self.video_negative_prompt.text()
        )

        request.duration = int(
            self.duration.currentText().split()[0]
        )

        request.fps = int(
            self.fps.currentText().split()[0]
        )

        request.model = "LTX Video"

        self.generate_requested.emit(request)

    def set_image(self, path):

        self.image_path.setText(path)

        self.generate.setEnabled(True)