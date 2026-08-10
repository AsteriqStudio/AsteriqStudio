from backends.backend import Backend

from backends.comfy_client import ComfyClient
from backends.video_history_parser import VideoHistoryParser
from backends.workflow_loader import WorkflowLoader
from backends.workflow_editor import WorkflowEditor
from backends.history_parser import HistoryParser
from backends.output_manager import OutputManager
from backends.image_importer import ImageImporter

from models.generation_request import GenerationRequest
from .comfy_input_manager import ComfyInputManager

from .video_workflow_editor import VideoWorkflowEditor
import random


class ComfyBackend(Backend):

    def __init__(self):

        self.client = ComfyClient()

        self.loader = WorkflowLoader()

        self.output = OutputManager()

        self.importer = ImageImporter()

        self.video_editor = VideoWorkflowEditor()

        # >N
        self.video_history = VideoHistoryParser()

        self.comfy_input = ComfyInputManager()

    def generate_image(
        self,
        request: GenerationRequest
    ):

        print("=" * 50)
        print("COMFY BACKEND")
        print("=" * 50)

        print("1. Loading workflow")

        workflow = self.loader.load(
            "image/sdxl_turbo_api.json"
        )

        print("2. Preparing workflow")

        # Build the final prompt
        prompt = request.image_prompt.strip()

        if request.style:
            prompt = f"{prompt}, {request.style}"

        seed = request.seed

        if seed < 0:
            seed = random.randint(0, 2**63 - 1)

        print("Using seed:", seed)

        workflow = WorkflowEditor.prepare(
            workflow,
            prompt=prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
            seed=seed
        )

        print("3. Sending workflow")

        prompt_id = self.client.generate(workflow)

        print("Prompt ID:", prompt_id)

        print("4. Waiting for image")

        history = self.client.wait_for_image(prompt_id)

        print("5. History received")

        image = HistoryParser.get_image(history)

        print("Image:", image)

        print("6. Finding output path")

        path = self.output.image_path(image)

        print(path)

        print("7. Importing")

        new_path = self.importer.copy(
            path,
            "Projects/Default/Images"
        )

        print("Finished")

        return new_path

    def generate_video(self, request):

        # Copy the selected image into ComfyUI's input folder
        image_filename = self.comfy_input.copy_image(
            request.image_path
        )

        # Load the workflow
        workflow = self.loader.load(
            "video/ltx_image_to_video.json"
        )

        # Edit workflow with the user's settings
        workflow = self.video_editor.prepare(
            workflow,
            request,
            image_filename
        )

        # Send to ComfyUI
        prompt_id = self.client.generate(workflow)

        # Wait until generation finishes
        history = self.client.wait_for_video(prompt_id)

        # Get generated video
        video = self.video_history.get_video(history)

        # Find the actual ComfyUI output
        path = self.output.video_path(video)

        # Import into Asteriq project
        new_path = self.importer.copy(
            path,
            "Projects/Default/Videos"
        )

        return new_path

    def health_check(self):

        return True
        
    def health_check(self):

        return True

    def available_models(self):

        return [
            "SDXL Turbo",
            "LTX Video"
        ]