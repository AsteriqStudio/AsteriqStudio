from video.video_generator import VideoGenerator
from video.video_service import VideoService

generator = VideoGenerator()

service = VideoService(generator)

video = service.generate(
    prompt="A cinematic samurai walking through a bamboo forest",
    image_path="Projects/Default/Images/test.png"
)

print(video)