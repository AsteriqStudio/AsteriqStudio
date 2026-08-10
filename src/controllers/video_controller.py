from services.video_service import VideoService


class VideoController:

    def __init__(self):
        self.service = VideoService()

    def generate(self, request):
        return self.service.generate(request)