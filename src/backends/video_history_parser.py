class VideoHistoryParser:

    @staticmethod
    def get_video(history):

        outputs = history.get("outputs", {})

        # SaveVideo node
        save_video = outputs.get("81")

        if not save_video:
            raise RuntimeError(
                "Video output node 81 was not found in ComfyUI history."
            )

        # ComfyUI SaveVideo output
        videos = save_video.get("videos", [])

        if not videos:
            raise RuntimeError(
                "ComfyUI completed the workflow but no video was found."
            )

        return videos[0]