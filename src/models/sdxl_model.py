from diffusers import DiffusionPipeline
from pathlib import Path
from datetime import datetime
import torch
from managers.project_manager import ProjectManager


class SDXLModel:

    def __init__(self):

        print("Loading SDXL Turbo...")

        self.project = ProjectManager()

        Path("outputs").mkdir(exist_ok=True)

        self.pipe = DiffusionPipeline.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=torch.float32
        )

        self.pipe.to("cpu")

        print("Model Ready!")

        

    def generate(self, prompt):

        print("Preparing generation...")

        image = self.pipe(
            prompt=prompt,
            num_inference_steps=2,
            guidance_scale=0.0
        ).images[0]

        print("Image generated.")

        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"

        path = self.project.get_image_path(filename)

        image.save(path)

        return str(path)