class VideoService:

    def __init__(self, generator):

        self.generator = generator

    def generate(
        self,
        prompt,
        image_path=None,
        output_path=None
    ):

        return self.generator.generate(
            prompt,
            image_path,
            output_path
        )