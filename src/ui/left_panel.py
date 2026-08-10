from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QComboBox,
    QLineEdit,
)

from models.generation_request import GenerationRequest


class LeftPanel(QWidget):

    generate_requested = Signal(object)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # -----------------------------
        # Title
        # -----------------------------

        title = QLabel("Image Generation")

        layout.addWidget(title)

        # -----------------------------
        # Prompt
        # -----------------------------

        layout.addWidget(QLabel("Prompt"))

        self.prompt = QTextEdit()

        self.prompt.setPlaceholderText(
            "Describe the image you want to create..."
        )

        layout.addWidget(self.prompt)

        # -----------------------------
        # Negative Prompt
        # -----------------------------

        layout.addWidget(QLabel("Negative Prompt"))

        self.negative_prompt = QTextEdit()

        layout.addWidget(self.negative_prompt)

        # -----------------------------
        # Style
        # -----------------------------

        layout.addWidget(QLabel("Style"))

        self.style = QComboBox()

        self.style.addItems([
            "Photorealistic",
            "Cinematic",
            "Anime",
            "Fantasy",
            "Cyberpunk",
            "Documentary"
        ])

        layout.addWidget(self.style)

        # -----------------------------
        # Image Model
        # -----------------------------

        layout.addWidget(QLabel("Image Model"))

        self.model = QComboBox()

        self.model.addItems([
            "SDXL Turbo"
        ])

        layout.addWidget(self.model)

        # -----------------------------
        # Output
        # -----------------------------

        layout.addWidget(QLabel("Output"))

        self.output = QComboBox()

        self.output.addItems([
            "Square",
            "Portrait",
            "Landscape",
            "TikTok",
            "Instagram Reel",
            "YouTube 1080p",
            "YouTube 4K"
        ])

        layout.addWidget(self.output)

        # -----------------------------
        # Seed
        # -----------------------------

        layout.addWidget(QLabel("Seed"))

        self.seed = QLineEdit("-1")

        layout.addWidget(self.seed)

        layout.addStretch()

        # -----------------------------
        # Generate Button
        # -----------------------------

        self.generate = QPushButton(
            "Generate Image"
        )

        layout.addWidget(self.generate)

        self.setLayout(layout)

        self.generate.clicked.connect(
            self.generate_image
        )

    def generate_image(self):

        request = GenerationRequest()

        request.image_prompt = (
            self.prompt.toPlainText()
        )

        request.image_negative_prompt = (
            self.negative_prompt.toPlainText()
        )

        request.style = self.style.currentText()

        request.model = (
            self.model.currentText()
        )

        output = self.output.currentText()

        if output == "Square":
            request.width = 1024
            request.height = 1024

        elif output == "Portrait":
            request.width = 832
            request.height = 1216

        elif output == "Landscape":
            request.width = 1216
            request.height = 832

        elif output == "TikTok":
            request.width = 1080
            request.height = 1920

        elif output == "Instagram Reel":
            request.width = 1080
            request.height = 1920

        elif output == "YouTube 1080p":
            request.width = 1920
            request.height = 1080

        elif output == "YouTube 4K":
            request.width = 3840
            request.height = 2160

        try:
            request.seed = int(
                self.seed.text()
            )
        except ValueError:
            request.seed = -1

        self.generate_requested.emit(request)