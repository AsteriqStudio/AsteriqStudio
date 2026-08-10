import time
import requests


class ComfyClient:

    def __init__(self):
        self.url = "http://127.0.0.1:8188"

    def is_running(self):

        try:
            r = requests.get(
                self.url + "/system_stats",
                timeout=2
            )

            return r.status_code == 200

        except:
            return False

    def generate(self, workflow):

        response = requests.post(
            self.url + "/prompt",
            json={
                "prompt": workflow
            }
        )

        print("=" * 50)
        print("COMFY RESPONSE")
        print("=" * 50)
        print("Status:", response.status_code)

        try:
            print(response.json())
        except Exception:
            print(response.text)

        response.raise_for_status()

        return response.json()["prompt_id"]

    def get_history(self, prompt_id):

        r = requests.get(
            self.url + "/history/" + prompt_id
        )

        return r.json()

    def wait_for_image(self, prompt_id):

        while True:

            history = self.get_history(prompt_id)

            if prompt_id in history:
                return history[prompt_id]

            time.sleep(0.5)


    def wait_for_video(self, prompt_id):

        while True:

            history = self.get_history(prompt_id)

            if prompt_id in history:

                result = history[prompt_id]

                status = result.get("status", {})
                status_str = status.get("status_str", "")

                if status_str == "error":

                    messages = status.get("messages", [])

                    raise RuntimeError(
                        f"ComfyUI video generation failed: {messages}"
                    )

                if status_str in ("success", "completed"):

                    return result

                # History exists, but ComfyUI has not finished yet.
                # Continue waiting.

            time.sleep(0.5)