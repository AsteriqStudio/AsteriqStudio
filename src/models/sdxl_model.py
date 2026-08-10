from diffusers import DiffusionPipeline
from pathlib import Path
from datetime import datetime
import torch
from managers.project_manager import ProjectManager

from config.generation_settings import GenerationSettings


class SDXLModel:

    def __init__(self):

        self.settings = GenerationSettings()

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
            negative_prompt=self.settings.negative_prompt,
            width=self.settings.width,
            height=self.settings.height,
            num_inference_steps=self.settings.steps,
            guidance_scale=self.settings.guidance,
            generator=None if self.settings.seed is None else torch.Generator("cpu").manual_seed(self.settings.seed)
        ).images[0]

        print("Image generated.")

        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"

        path = self.project.get_image_path(filename)

        image.save(path)

        return str(path)