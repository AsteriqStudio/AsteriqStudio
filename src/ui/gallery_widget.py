from pathlib import Path
from sys import path

from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal

from PySide6.QtGui import QIcon
from tomlkit import item


class GalleryWidget(QListWidget):

    image_selected = Signal(str)

    def __init__(self):
        super().__init__()

        self.setIconSize(self.iconSize())

        self.refresh()

        self.itemClicked.connect(self.image_clicked)

    def refresh(self):

        self.clear()

        image_folder = Path("Projects/Default/Images")

        images = sorted(
            image_folder.glob("*.png"),
            reverse=True
        )

        for image in images:

            item = QListWidgetItem(image.stem)

            item.setIcon(QIcon(str(image)))

            item.setData(256, str(image))

            self.addItem(item)


    def image_clicked(self, item):

        path = item.data(256)

        self.image_selected.emit(path)