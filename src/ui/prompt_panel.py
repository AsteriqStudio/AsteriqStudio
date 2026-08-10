from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QComboBox,
    QPushButton,
    QLineEdit,
)

from PySide6.QtCore import Signal

from models.generation_request import GenerationRequest


class PromptPanel(QWidget):

    generate_requested = Signal(object)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Prompt"))

        self.prompt = QTextEdit()
        layout.addWidget(self.prompt)

        layout.addWidget(QLabel("Negative Prompt"))

        self.negative = QTextEdit()
        layout.addWidget(self.negative)

        layout.addWidget(QLabel("Style"))

        self.style = QComboBox()

        self.style.addItems([
            "Cinematic",
            "Photorealistic",
            "Fantasy",
            "Anime",
            "Cyberpunk",
            "Documentary"
        ])

        layout.addWidget(self.style)

        layout.addWidget(QLabel("Model"))

        self.model = QComboBox()

        self.model.addItems([
            "SDXL Turbo"
        ])

        layout.addWidget(self.model)

        layout.addWidget(QLabel("Output"))

        self.output = QComboBox()

        self.output.addItems([
            "Square",
            "Portrait",
            "Landscape",
            "YouTube 1080p",
            "YouTube 4K",
            "TikTok",
            "Instagram Reel"
        ])

        layout.addWidget(self.output)

        layout.addWidget(QLabel("Seed"))

        self.seed = QLineEdit("-1")

        layout.addWidget(self.seed)

        self.generate = QPushButton("Generate")

        layout.addWidget(self.generate)

        layout.addStretch()

        self.generate.clicked.connect(
            self.emit_generate
        )

        self.setLayout(layout)

    def emit_generate(self):

        request = GenerationRequest()

        request.image_prompt = self.prompt.toPlainText()

        request.image_negative_prompt = (
            self.negative.toPlainText()
        )

        request.model = self.model.currentText()

        try:
            request.seed = int(self.seed.text())
        except ValueError:
            request.seed = -1

        self.generate_requested.emit(request)