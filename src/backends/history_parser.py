class HistoryParser:

    @staticmethod
    def get_image(history):

        outputs = history["outputs"]

        for node in outputs.values():

            if "images" in node:

                image = node["images"][0]

                return {
                    "filename": image["filename"],
                    "subfolder": image["subfolder"],
                    "type": image["type"],
                }

        return None