from PySide6.QtWidgets import (
    QWidget,
    QStackedWidget,
    QVBoxLayout,
)


class WorkspacePanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.stack = QStackedWidget()

        layout.addWidget(self.stack)

    def add_page(self, widget):

        self.stack.addWidget(widget)

    def set_page(self, index):

        self.stack.setCurrentIndex(index)