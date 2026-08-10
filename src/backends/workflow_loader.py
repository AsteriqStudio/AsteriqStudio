import json
from pathlib import Path


class WorkflowLoader:

    def __init__(self):
        self.folder = Path("workflows")

    def load(self, name):

        path = self.folder / name

        if not path.exists():
            raise FileNotFoundError(
                f"Workflow '{name}' was not found in '{self.folder}'."
            )

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)