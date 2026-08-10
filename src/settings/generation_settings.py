from config.resolutions import RESOLUTIONS


class GenerationSettings:

    def __init__(self):

        self.model = "SDXL Turbo"

        self.width, self.height = RESOLUTIONS["Square 512"]

        self.steps = 2

        self.guidance = 0.0

        self.seed = -1

        self.negative_prompt = ""