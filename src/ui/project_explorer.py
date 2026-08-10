from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QInputDialog,
)


class ProjectExplorer(QWidget):

    project_changed = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Projects"))

        self.projects = QListWidget()

        layout.addWidget(self.projects)

        self.new_project = QPushButton("New Project")

        layout.addWidget(self.new_project)

        self.setLayout(layout)

        self.refresh()

        self.projects.itemClicked.connect(self.change_project)

        self.new_project.clicked.connect(self.create_project)

    def refresh(self):

        self.projects.clear()

        Path("Projects").mkdir(exist_ok=True)

        for folder in sorted(Path("Projects").iterdir()):

            if folder.is_dir():

                self.projects.addItem(folder.name)

    def change_project(self, item):

        self.project_changed.emit(item.text())

    def create_project(self):

        name, ok = QInputDialog.getText(
            self,
            "New Project",
            "Project name:"
        )

        if ok and name:

            root = Path("Projects") / name

            (root / "Images").mkdir(parents=True, exist_ok=True)
            (root / "Videos").mkdir(exist_ok=True)
            (root / "Audio").mkdir(exist_ok=True)
            (root / "Exports").mkdir(exist_ok=True)

            self.refresh()