from dataclasses import dataclass


@dataclass
class GenerationSettings:

    model: str = "SDXL Turbo"

    width: int = 512

    height: int = 512

    steps: int = 2

    guidance: float = 0.0

    seed: int = -1

    negative_prompt: str = ""