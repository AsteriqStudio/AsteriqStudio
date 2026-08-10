from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
)


class NavigationPanel(QWidget):

    page_changed = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        pages = [
            ("🖼 Assets", "assets"),
            ("✨ Generate", "generate"),
            ("🎥 Video", "video"),
            ("🎵 Audio", "audio"),
            ("📋 Queue", "queue"),
            ("📜 Console", "console"),
            ("⚙ Settings", "settings"),
        ]

        for text, page in pages:

            button = QPushButton(text)

            button.clicked.connect(
                lambda checked=False, p=page:
                self.page_changed.emit(p)
            )

            layout.addWidget(button)

        layout.addStretch()