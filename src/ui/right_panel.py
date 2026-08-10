from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QProgressBar,
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl
from torch import layout


class RightPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.status = QLabel("Ready")

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()

        self.preview = QLabel()

        # ---------- Video ----------
        self.video = QVideoWidget()
        self.video.setMinimumSize(800, 600)
        self.video.hide()

        self.player = QMediaPlayer()
        self.audio = QAudioOutput()

        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        # ---------------------------

        self.preview.setMinimumSize(800, 600)
        self.preview.setAlignment(Qt.AlignCenter)

        self.preview.setStyleSheet("""
            background:#1f1f1f;
            border:2px solid #555;
        """)

        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addWidget(self.preview)
        layout.addWidget(self.preview)

        layout.addWidget(self.video)

        self.setLayout(layout)

    def display_image(self, path):

        self.player.stop()

        self.video.hide()

        self.preview.show()

        pixmap = QPixmap(path)

        pixmap = pixmap.scaled(
            self.preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.preview.setPixmap(pixmap)

    def display_video(self, path):

        self.preview.hide()

        self.video.show()

        self.player.setSource(
            QUrl.fromLocalFile(path)
        )

        self.player.play()