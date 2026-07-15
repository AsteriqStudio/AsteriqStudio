from models.sdxl_model import SDXLModel


class ModelRegistry:

    MODELS = {
        "SDXL Turbo": SDXLModel,
    }

    @classmethod
    def get_model(cls, name):

        return cls.MODELS[name]()