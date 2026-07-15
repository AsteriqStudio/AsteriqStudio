from pathlib import Path


class ProjectManager:

    def __init__(self, project_name="Default"):

        self.project_name = project_name

        self.root = Path("Projects") / project_name

        self.images = self.root / "Images"
        self.videos = self.root / "Videos"
        self.audio = self.root / "Audio"
        self.exports = self.root / "Exports"

        self.create_structure()

    def create_structure(self):

        self.images.mkdir(parents=True, exist_ok=True)
        self.videos.mkdir(parents=True, exist_ok=True)
        self.audio.mkdir(parents=True, exist_ok=True)
        self.exports.mkdir(parents=True, exist_ok=True)

    def get_image_path(self, filename):

        return self.images / filename

    def get_video_path(self, filename):

        return self.videos / filename

    def get_audio_path(self, filename):

        return self.audio / filename

    def get_export_path(self, filename):

        return self.exports / filename