import json
import urllib.request


class ComfyClient:

    def __init__(self):

        self.server = "http://127.0.0.1:8188"

    def queue_prompt(self, workflow):

        body = json.dumps({
            "prompt": workflow
        }).encode("utf-8")

        request = urllib.request.Request(
            self.server + "/prompt",
            data=body,
            headers={
                "Content-Type": "application/json"
            }
        )

        response = urllib.request.urlopen(request)

        return json.loads(response.read())