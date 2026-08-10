from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
)


class StatusBar(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.status = QLabel("Ready")

        self.backend = QLabel("Local")

        self.queue = QLabel("Queue: 0")

        layout.addWidget(self.status)

        layout.addStretch()

        layout.addWidget(self.backend)

        layout.addWidget(self.queue)