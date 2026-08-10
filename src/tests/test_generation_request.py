import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.generation_request import GenerationRequest


def main():

    request = GenerationRequest()

    print("=" * 60)
    print("GenerationRequest Test")
    print("=" * 60)

    print(request)

    print()

    print("Image Prompt:", request.image_prompt)
    print("Video Prompt:", request.video_prompt)
    print("Width:", request.width)
    print("Height:", request.height)
    print("Steps:", request.steps)
    print("Seed:", request.seed)
    print("Duration:", request.duration)
    print("FPS:", request.fps)
    print("Model:", request.model)


if __name__ == "__main__":
    main()