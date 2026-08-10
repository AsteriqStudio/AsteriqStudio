from PySide6.QtWidgets import QListWidget

from prompts.preset_manager import PromptPresetManager


class PresetWidget(QListWidget):

    def __init__(self):

        super().__init__()

        self.manager = PromptPresetManager()

        for preset in self.manager.all():

            self.addItem(preset.name)