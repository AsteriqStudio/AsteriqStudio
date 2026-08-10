import random

class VideoWorkflowEditor:

    def prepare(self, workflow, request, image_filename):

        # Motion / video prompt
        workflow["6"]["inputs"]["text"] = request.video_prompt

        # Negative motion prompt
        workflow["7"]["inputs"]["text"] = request.video_negative_prompt

        # Convert duration to frames
        target_frames = request.duration * request.fps

        # LTX frame count must follow 8n + 1
        frames = ((target_frames - 1 + 7) // 8) * 8 + 1


        # Image-to-video settings
        workflow["77"]["inputs"]["width"] = request.width
        workflow["77"]["inputs"]["height"] = request.height
        workflow["77"]["inputs"]["length"] = frames

        # FPS
        workflow["69"]["inputs"]["frame_rate"] = request.fps
        workflow["80"]["inputs"]["fps"] = request.fps

        # Steps
        #workflow["71"]["inputs"]["steps"] = request.steps

        # Seed
        seed = request.seed

        if seed < 0:
            seed = random.randint(
                0,
                18446744073709551615
            )

        workflow["72"]["inputs"]["noise_seed"] = seed

        # Starting image
        workflow["78"]["inputs"]["image"] = image_filename

        return workflow