from pathlib import Path


class OutputManager:

    def __init__(self):

        self.output = Path.home() / "AppData" / "Local" / "Comfy-Desktop" / "ComfyUI-Shared" / "output"

    def image_path(self, image):

        return self.output / image["subfolder"] / image["filename"]

    def video_path(self, video):

        return self.output / video["subfolder"] / video["filename"]