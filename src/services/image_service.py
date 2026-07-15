from core.generator import Generator


class ImageService:

    def __init__(self):

        self.generator = Generator()

    def generate(self, prompt):

        print("=" * 50)
        print("IMAGE SERVICE")
        print("=" * 50)

        return self.generator.generate(prompt)