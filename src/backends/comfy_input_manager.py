from pathlib import Path
import shutil


class ComfyInputManager:

    def __init__(self):
        self.input = (
            Path.home()
            / "AppData"
            / "Local"
            / "Comfy-Desktop"
            / "ComfyUI-Shared"
            / "input"
        )

    def copy_image(self, image_path):

        source = Path(image_path)

        if not source.exists():
            raise FileNotFoundError(
                f"Input image not found: {source}"
            )

        self.input.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = self.input / source.name

        shutil.copy2(
            source,
            destination
        )

        return source.name