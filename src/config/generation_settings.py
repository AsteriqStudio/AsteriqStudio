class GenerationSettings:

    def __init__(self):

        self.width = 512
        self.height = 512

        self.steps = 2

        self.guidance = 0.0

        self.seed = None

        self.negative_prompt = ""

        self.model = "SDXL Turbo"