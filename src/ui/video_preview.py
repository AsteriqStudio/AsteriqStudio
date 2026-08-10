from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class VideoPreview(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.preview = QLabel("No video generated")

        self.preview.setAlignment(Qt.AlignCenter)

        self.preview.setMinimumHeight(350)

        self.preview.setStyleSheet("""
            QLabel{
                border:2px solid gray;
                border-radius:10px;
                background:#1f1f1f;
                color:white;
            }
        """)

        layout.addWidget(self.preview)

        self.setLayout(layout)