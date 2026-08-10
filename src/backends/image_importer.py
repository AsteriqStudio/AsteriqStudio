import shutil
from pathlib import Path


class ImageImporter:

    def copy(self, source, destination_folder):

        destination = Path(destination_folder)

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        new_path = destination / Path(source).name

        shutil.copy2(source, new_path)

        return str(new_path)