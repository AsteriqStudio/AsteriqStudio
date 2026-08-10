from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from ui.layouts.workspace_panel import WorkspacePanel
from ui.left_panel import LeftPanel
from ui.asset_browser import AssetBrowser
from ui.queue_widget import QueueWidget
from ui.video_panel import VideoPanel


class Workspace(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.stack = WorkspacePanel()

        self.prompt = LeftPanel()
        self.assets = AssetBrowser()
        self.queue = QueueWidget()
        self.video = VideoPanel()
        self.console = QWidget()

        self.stack.add_page(self.prompt)
        self.stack.add_page(self.assets)
        self.stack.add_page(self.queue)
        self.stack.add_page(self.video)
        self.stack.add_page(self.console)

        layout.addWidget(self.stack)

    def set_page(self, index):
        self.stack.set_page(index)