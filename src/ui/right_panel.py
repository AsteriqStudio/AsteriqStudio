from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QProgressBar,
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class RightPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.status = QLabel("Ready")

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()

        self.preview = QLabel()

        self.preview.setMinimumSize(800, 600)
        self.preview.setAlignment(Qt.AlignCenter)

        self.preview.setStyleSheet("""
            background:#1f1f1f;
            border:2px solid #555;
        """)

        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addWidget(self.preview)

        self.setLayout(layout)

    def display_image(self, path):

        pixmap = QPixmap(path)

        pixmap = pixmap.scaled(
            self.preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.preview.setPixmap(pixmap)