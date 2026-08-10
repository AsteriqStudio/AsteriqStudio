from pathlib import Path
from datetime import datetime

from video.base_video_generator import BaseVideoGenerator


class VideoGenerator(BaseVideoGenerator):

    def generate(
        self,
        prompt,
        image_path=None,
        output_path=None
    ):

        print("=" * 50)
        print("VIDEO GENERATION")
        print("=" * 50)

        print("Prompt:")
        print(prompt)

        print()

        print("Image:")
        print(image_path)

        print()

        filename = datetime.now().strftime("%Y%m%d_%H%M%S")

        output = Path("Projects/Default/Videos")

        output.mkdir(parents=True, exist_ok=True)

        output = output / f"{filename}.mp4"

        print("Output:")

        print(output)

        return str(output)