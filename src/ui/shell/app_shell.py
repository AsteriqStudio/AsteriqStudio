from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

PAGES = {
    "generate": 0,
    "assets": 1,
    "queue": 2,
    "video": 3,
    "console": 4,
}

from ui.navigation.navigation_panel import NavigationPanel
from ui.workspace import Workspace
from ui.right_panel import RightPanel
from ui.status.status_bar import StatusBar


class AppShell(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        # Header
        header = QLabel("AsteriqStudio")

        header.setObjectName("header")

        root.addWidget(header)

        # Center

        center = QHBoxLayout()

        self.navigation = NavigationPanel()

        self.workspace = Workspace()

        self.right = RightPanel()

        center.addWidget(self.navigation, 1)
        center.addWidget(self.workspace, 4)
        center.addWidget(self.right, 2)

        root.addLayout(center)

        # Bottom

        self.statusbar = StatusBar()

        root.addWidget(self.statusbar)


        self.navigation.page_changed.connect(self.change_page)

    def change_page(self, page):

        if page in PAGES:
            self.workspace.set_page(PAGES[page])