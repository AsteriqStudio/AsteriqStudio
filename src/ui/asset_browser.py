from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QVBoxLayout,
    QComboBox,
)


class AssetBrowser(QWidget):

    asset_selected = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Assets"))

        self.asset_type = QComboBox()

        self.asset_type.addItems([
            "Images",
            "Videos",
            "Audio",
            "Characters",
            "Exports"
        ])

        layout.addWidget(self.asset_type)

        self.list = QListWidget()

        layout.addWidget(self.list)

        self.setLayout(layout)

        self.asset_type.currentTextChanged.connect(self.refresh)

        self.list.itemClicked.connect(self.item_clicked)

        self.refresh()

    def refresh(self):

        self.list.clear()

        asset = self.asset_type.currentText()

        folder = Path("Projects/Default") / asset

        folder.mkdir(parents=True, exist_ok=True)

        extensions = {
            "Images": ["*.png", "*.jpg", "*.jpeg", "*.webp"],
            "Videos": ["*.mp4", "*.mov", "*.avi", "*.mkv"],
            "Audio": ["*.mp3", "*.wav", "*.ogg"],
            "Exports": ["*"],
            "Characters": ["*"]
        }

        files = []

        for pattern in extensions.get(asset, ["*"]):
            files.extend(folder.glob(pattern))

        files = sorted(files, reverse=True)

        for file in files:

            item = QListWidgetItem(file.stem)

            if asset == "Images":
                item.setIcon(QIcon(str(file)))

            item.setData(Qt.UserRole, str(file))

            self.list.addItem(item)

    def item_clicked(self, item):

        path = item.data(Qt.UserRole)

        self.asset_selected.emit(path)