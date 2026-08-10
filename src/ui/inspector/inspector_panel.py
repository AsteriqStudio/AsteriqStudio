from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QFormLayout,
)


class InspectorPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QFormLayout(self)

        self.name = QLabel("-")
        self.type = QLabel("-")
        self.size = QLabel("-")
        self.info = QLabel("-")

        layout.addRow("Name", self.name)
        layout.addRow("Type", self.type)
        layout.addRow("Size", self.size)
        layout.addRow("Info", self.info)