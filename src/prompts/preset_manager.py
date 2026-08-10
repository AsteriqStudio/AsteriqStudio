from prompts.preset import PromptPreset


class PromptPresetManager:

    def __init__(self):

        self.presets = [

            PromptPreset(
                "Portrait",
                "Ultra realistic portrait, detailed skin, cinematic lighting"
            ),

            PromptPreset(
                "Landscape",
                "Epic landscape, volumetric lighting, masterpiece"
            ),

            PromptPreset(
                "Product",
                "Professional product photography, studio lighting"
            ),

            PromptPreset(
                "Concept Art",
                "Concept art, highly detailed, trending on ArtStation"
            ),

            PromptPreset(
                "Cinematic",
                "Cinematic movie still, dramatic lighting, shallow depth of field"
            )

        ]

    def all(self):

        return self.presets