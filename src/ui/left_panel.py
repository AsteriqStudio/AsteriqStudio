from click import prompt

from PySide6.QtCore import Signal
from ui.gallery_widget import GalleryWidget

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QComboBox,
    QSpinBox,
)


class LeftPanel(QWidget):

    generate_requested = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Video Settings")

        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText(
            "A cinematic drone shot flying over snow covered mountains during sunrise..."
        )

        self.model = QComboBox()
        self.model.addItems([
            "LTX Video",
            "Wan 2.1",
            "Hunyuan"
        ])

        self.style = QComboBox()
        self.style.addItems([
            "Cinematic",
            "Realistic",
            "Anime",
            "Horror",
            "Documentary"
        ])

        self.duration = QSpinBox()
        self.duration.setRange(1, 30)
        self.duration.setValue(5)

        self.generate = QPushButton("Generate Video")

        layout.addWidget(title)
        layout.addWidget(QLabel("Prompt"))
        layout.addWidget(self.prompt)

        layout.addWidget(QLabel("Model"))
        layout.addWidget(self.model)

        layout.addWidget(QLabel("Style"))
        layout.addWidget(self.style)

        layout.addWidget(QLabel("Duration (seconds)"))
        layout.addWidget(self.duration)

        layout.addStretch()

        layout.addWidget(self.generate)

        self.setLayout(layout)


        self.generate.clicked.connect(self.generate_video)

    # 👇 This must be OUTSIDE __init__
    def generate_video(self):

        prompt = self.prompt.toPlainText()

        self.generate_requested.emit(prompt)